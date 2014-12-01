#     Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import boto
import lxml.html as LH
import lxml.html.clean as clean
import os
import re
import json
import requests

from requests import post
from boto.s3.key import Key
from boto.s3.connection import OrdinaryCallingFormat
from subprocess32 import PIPE
from collections import defaultdict
from sketchy import db, app, celery
from sketchy.models.capture import Capture
from sketchy.controllers.validators import grab_domain
import subprocess32


@celery.task(name='check_url', bind=True)
def check_url(self, capture_id=0, retries=0):
    """
    Check if a URL exists without downloading the whole file.
    We only check the URL header.
    """
    capture_record = Capture.query.filter(Capture.id == capture_id).first()
    capture_record.job_status = 'STARTED'
    # Write the number of retries to the capture record
    db.session.add(capture_record)
    capture_record.retry = retries
    db.session.commit()
    # Only retrieve the headers of the request, and return respsone code
    try:
        response = ""
        verify_ssl = app.config['SSL_HOST_VALIDATION']
        response = requests.get(capture_record.url, verify=verify_ssl, allow_redirects=False, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:28.0) Gecko/20100101 Firefox/28.0"})
        capture_record.url_response_code = response.status_code
        if capture_record.status_only:
            capture_record.job_status = 'COMPLETED'
            capture_record.capture_status = '%s HTTP STATUS CODE' % (response.status_code)
            if capture_record.callback:
                finisher(capture_record)
        else:
            capture_record.capture_status = '%s HTTP STATUS CODE' % (response.status_code)
    # If URL doesn't return a valid status code or times out, raise an exception
    except Exception as err:
        capture_record.job_status = 'RETRY'
        capture_record.capture_status = str(err.message)
        capture_record.url_response_code = 0

        check_url.retry(kwargs={'capture_id': capture_id, 'retries': capture_record.retry + 1}, exc=err, countdown=app.config['COOLDOWN'], max_retries=app.config['MAX_RETRIES'])

    # If the code was not a good code, record the status as a 404 and raise an exception
    finally:
        db.session.commit()
    return str(response.status_code)


def do_capture(status_code, capture_record, base_url):
    """
    Create a screenshot, text scrape, and html file for provided capture_record url.

    This depends on phantomjs and an associated javascript file to perform the captures.
    In the event an error occurs, an exception is raised and handled by the celery task
    or the controller that called this method.

    """
    # Make sure the capture_record
    db.session.add(capture_record)
    capture_name = grab_domain(capture_record.url) + '_' + str(capture_record.id)
    service_args = [
        app.config['PHANTOMJS'],
        '--ssl-protocol=any',
        '--ignore-ssl-errors=yes',
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/assets/capture.js',
        capture_record.url,
        os.path.join(app.config['LOCAL_STORAGE_FOLDER'], capture_name)]

    # Using subprocess32 backport, call phantom and if process hangs kill it
    pid = subprocess32.Popen(service_args, stdout=PIPE, stderr=PIPE)
    try:
        stdout, stderr = pid.communicate(timeout=35)
    except subprocess32.TimeoutExpired:
        pid.kill()
        stdout, stderr = pid.communicate()
        app.logger.error('PhantomJS Capture timeout')
        raise Exception('PhantomJS Capture timeout')

    # If the subprocess has an error, raise an exception
    if stderr or stdout:
        raise Exception(stderr)

    # Strip tags and parse out all text
    ignore_tags = ('script', 'noscript', 'style')
    with open(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], capture_name + '.html'), 'r') as content_file:
        content = content_file.read()
    cleaner = clean.Cleaner()
    content = cleaner.clean_html(content)
    doc = LH.fromstring(content)
    output = ""
    for elt in doc.iterdescendants():
        if elt.tag in ignore_tags:
            continue
        text = elt.text or ''
        tail = elt.tail or ''
        wordz = " ".join((text, tail)).strip('\t')

        if wordz and len(wordz) >= 2 and not re.match("^[ \t\n]*$", wordz):
            output += wordz.encode('utf-8')

    # Wite our html text that was parsed into our capture folder
    parsed_text = open(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], capture_name + '.txt'), 'wb')
    parsed_text.write(output)

    # Update the sketch record with the local URLs for the sketch, scrape, and html captures
    capture_record.sketch_url = base_url + '/files/' + capture_name + '.png'
    capture_record.scrape_url = base_url + '/files/' + capture_name + '.txt'
    capture_record.html_url = base_url + '/files/' + capture_name + '.html'

    # Create a dict that contains what files may need to be written to S3
    files_to_write = defaultdict(list)
    files_to_write['sketch'] = capture_name + '.png'
    files_to_write['scrape'] = capture_name + '.txt'
    files_to_write['html'] = capture_name + '.html'

    # If we are not writing to S3, update the capture_status that we are completed.
    if not app.config['USE_S3']:
        capture_record.job_status = "COMPLETED"
        capture_record.capture_status = "LOCAL_CAPTURES_CREATED"
    else:
        capture_record.capture_status = "LOCAL_CAPTURES_CREATED"
    db.session.commit()
    return files_to_write


def s3_save(files_to_write, capture_record):
    """
    Write a sketch, scrape, and html file to S3
    """
    db.session.add(capture_record)
    # These are the content-types for the files S3 will be serving up
    reponse_types = {'sketch': 'image/png', 'scrape': 'text/plain', 'html': 'text/html'}

    # Iterate through each file we need to write to s3
    for capture_type, file_name in files_to_write.items():
        # Connect to S3, generate Key, set path based on capture_type, write file to S3
        conn = boto.connect_s3(calling_format=OrdinaryCallingFormat())
        key = Key(conn.get_bucket(app.config.get('S3_BUCKET_PREFIX')))
        path = "sketchy/{}/{}".format(capture_type, capture_record.id)
        key.key = path
        key.set_contents_from_filename(app.config['LOCAL_STORAGE_FOLDER'] + '/' + file_name)

        # Generate a URL for downloading the files
        url = conn.generate_url(
            app.config.get('S3_LINK_EXPIRATION'),
            'GET',
            bucket=app.config.get('S3_BUCKET_PREFIX'),
            key=key.key,
            response_headers={
                'response-content-type': reponse_types[capture_type],
                'response-content-disposition': 'attachment; filename=' + file_name
            })

        # Generate appropriate url based on capture_type
        if capture_type == 'sketch':
            capture_record.sketch_url = str(url)
            # print capture_record.sketch_url
        if capture_type == 'scrape':
            capture_record.scrape_url = str(url)
            # print capture_record.scrape_url
        if capture_type == 'html':
            capture_record.html_url = str(url)
            # print capture_record.html_url

    # Remove local files if we are saving to S3
    os.remove(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], files_to_write['sketch']))
    os.remove(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], files_to_write['scrape']))
    os.remove(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], files_to_write['html']))

    # If we don't have a finisher we are donezo
    # TYPO********
    if capture_record.callback:
        capture_record.capture_status = 'S3_ITEMS_SAVED'
    else:
        capture_record.capture_status = 'S3_ITEMS_SAVED'
        capture_record.job_status = 'COMPLETED'
    db.session.commit()


def finisher(capture_record):
    """
    POST finished chain to a callback URL provided
    """
    db.session.add(capture_record)
    verify_ssl = app.config['SSL_HOST_VALIDATION']
    # Set the correct headers for the postback
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    req = post(capture_record.callback, verify=verify_ssl, data=json.dumps(capture_record.as_dict()), headers=headers)

    # If a 4xx or 5xx status is recived, raise an exception
    req.raise_for_status()

    # Update capture_record and save to database
    capture_record.job_status = 'COMPLETED'
    db.session.add(capture_record)
    db.session.commit()


@celery.task(name='celery_capture', ignore_result=True, bind=True)
def celery_capture(self, status_code, base_url, capture_id=0, retries=0):
    """
    Celery task used to create sketch, scrape, html.
    Task also writes files to S3 or posts a callback depending on configuration file.
    """
    capture_record = Capture.query.filter(Capture.id == capture_id).first()
    # Write the number of retries to the capture record
    db.session.add(capture_record)
    capture_record.retry = retries
    db.session.commit()

    try:
        # Perform a callback or complete the task depending on error code and config
        if capture_record.url_response_code > 400 and app.config['CAPTURE_ERRORS'] == False:
            if capture_record.callback:
                finisher(capture_record)
            else:
                capture_record.job_status = 'COMPLETED'
            return True
    except Exception as err:
        app.logger.error(err)
        capture_record.job_status = 'RETRY'
        capture_record.capture_status = str(err)
        capture_record.retry = retries + 1
        raise celery_capture.retry(args=[status_code, base_url],
            kwargs = { 'capture_id' :capture_id, 'retries': capture_record.retry + 1}, exc=err,
            countdown=app.config['COOLDOWN'],
            max_retries=app.config['MAX_RETRIES'])
    finally:
        db.session.commit()
    # First perform the captures, then either write to S3, perform a callback, or neither
    try:
        # call the main capture function to retrieve sketches, scrapes, and html
        files_to_write = do_capture(status_code, capture_record, base_url)
        # Call the s3 save funciton if s3 is configured, and perform callback if configured.
        if app.config['USE_S3']:
            if capture_record.callback:
                s3_save(files_to_write, capture_record)
                finisher(capture_record)
            else:
                s3_save(files_to_write, capture_record)
        elif capture_record.callback:
                finisher(capture_record)

    # Catch exceptions raised by any functions called
    except Exception as err:
        app.logger.error(err)
        capture_record.job_status = 'RETRY'
        capture_record.capture_status = str(err)
        capture_record.retry = retries + 1
        raise celery_capture.retry(args=[status_code, base_url],
            kwargs={'capture_id' :capture_id, 'retries': capture_record.retry + 1}, exc=err,
            countdown=app.config['COOLDOWN'],
            max_retries=app.config['MAX_RETRIES'])
    finally:
        db.session.commit()

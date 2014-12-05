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
import tasks

from sketchy import db, app
from sketchy.models.capture import Capture
from sketchy.controllers.validators import check_url, grab_domain
from flask import send_from_directory
from flask.ext.restful import Resource, reqparse
from celery import chain
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
# Request parser for API calls to Payload model
JSONPARSER = reqparse.RequestParser()
JSONPARSER.add_argument('url', type=str, required=True, help="URL Cannot Be Blank", location='json')
JSONPARSER.add_argument('status_only', type=bool, required=False, location='json')
JSONPARSER.add_argument('callback', type=str, required=False, location='json')

EAGERPARSER = reqparse.RequestParser()
EAGERPARSER.add_argument('url', type=str, required=True, help="URL cannot be blank", location='args')
EAGERPARSER.add_argument('type', type=str, required=True, help="Type of capture must be set: html, sketch, or scrape", location='args')


class CaptureView(Resource):
    """
    API Provides CRUD operations for Captures based on id.

    Methods:
    GET
    """
    def get(self, id):
        """
        Retrieve Captures based on id
        """
        capture_record = Capture.query.filter(Capture.id == id).first()
        if capture_record is not None:
            return capture_record.as_dict()
        else:
            return 'No capture found!', 404


class CaptureViewLast(Resource):
    """
    API Provides last capture in database.  

    Methods:
    GET
    """
    def get(self):
        """
        Retrieve Captures based on id
        """
        capture_record = Capture.query.order_by('-id').first()

        if capture_record is not None:
            return capture_record.as_dict()
        else:
            return 'No capture found!', 404

class CaptureStatic(Resource):
    """
    API Provides last capture in database.  

    Methods:
    GET
    """
    def post(self):
        """
        Retrieve Captures based on id
        """
        capture_record = Capture.query.order_by('-id').first()

        if capture_record is not None:
            return capture_record.as_dict()
        else:
            return 'No capture found!', 404

class CaptureViewList(Resource):
    """
    API Provides CRUD operations for Capturees.

    Methods:
    GET
    POST
    """
    def get(self):
        """
        Retrieve all sketch records the database
        """
        results = []
        for row in Capture.query.order_by(Capture.id.desc()).all():
            results.append(row.as_dict())

        return results

    def post(self):
        """
        Create a new sketch record and call celery tasks for populating record data
        """
        # Determine the hostname/port as well as scheme of webserver
        base_url = app.config['BASE_URL']

        # Parse out all arguments that may be provided by requestor
        args = JSONPARSER.parse_args()
        capture_record = Capture()
        capture_record.url = args["url"]
        capture_record.status_only = args["status_only"]
        capture_record.callback = args["callback"]

        # Add the capture_record and commit to the DB
        try:
            db.session.add(capture_record)
            db.session.commit()
        except IntegrityError, exc:
            return {"error": exc.message}, 500

        # Refresh capture_record to obtain an ID for record
        db.session.refresh(capture_record)

        # If status_only flag enabled, just capture status code from URL
        if capture_record.status_only is True:
            tasks.check_url.delay(capture_id=capture_record.id)
        else:
            # If the application is configured for S3 store contents in a bucket
            # This will first check if URL is valid, then sketch, scrape, and store files
            celery_sketch = chain(tasks.check_url.s(capture_id=capture_record.id),
                                  tasks.celery_capture.s(base_url, capture_id=capture_record.id, model='capture')
                                  ).apply_async()

        # Commit all changes to DB and return JSON
        db.session.commit()
        return capture_record.as_dict(), 201


class Eager(Resource):
    """
    Provides a way to retrieve a sketch, scrape, or html file eagerly (blocking call)

    Methods:
    GET

    Args:
    url = url to generate a text scrape.
    type = ['sketch', 'scrape', 'html'] string to specifiy capture tyope
    """
    def get(self):
        """
        Retrieve Capture based on id
        """
        args = EAGERPARSER.parse_args()
        base_url = app.config['BASE_URL']

        app.config.update(USE_S3='')
        # Parse out url and capture type
        capture_record = Capture()
        capture_record.url = args["url"]
        capture_type = args["type"]

        if capture_type not in ['html', 'sketch', 'scrape']:
                return 'Incorrect capture type specified: html, sketch, or scrape', 406

        # Write to DB
        try:
            db.session.add(capture_record)
            db.session.commit()
        except IntegrityError, exc:
            return {"error": exc.message}, 500

        # Refresh capture_record to obtain an ID for record
        db.session.refresh(capture_record)

        try:
            # dict of functions that generate capture names
            capture_names = {'html': grab_domain(capture_record.url) + '_' + str(capture_record.id) + '.html',
                             'sketch': grab_domain(capture_record.url) + '_' + str(capture_record.id) + '.png',
                             'scrape': grab_domain(capture_record.url) + '_' + str(capture_record.id) + '.txt'}
        except:
            return 'This is not a valid URL', 406

        # Check that url is valid and responsive
        if not check_url(capture_record):
            return 'Could not connect to URL', 406

        # file_to_write is a placeholder in eager calls
        file_to_write = {}

        try:
            # Call eager_capture to create scrape, sketch, and html file (blocking)
            files_to_write = tasks.do_capture(200, capture_record, base_url)

            if capture_type in capture_names:
                return send_from_directory(app.config['LOCAL_STORAGE_FOLDER'],
                                           capture_names[capture_type],
                                           as_attachment=True)
            else:
                return 'Incorrect capture type specified: html, sketch, or scrape', 406
        except Exception as err:
            # Consider updating capture_record status here
            app.logger.error(err)
            return str(err), 406

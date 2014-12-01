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
import requests
from sketchy import db, app
from tldextract import extract

def get_server_status_code(url):
    """
    Return the server's status code.
    """
    # Only retrieve the headers of the request, and return respsone code
    try:
        verify_ssl = app.config['SSL_HOST_VALIDATION']
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:28.0) Gecko/20100101 Firefox/28.0"}, verify=verify_ssl)
        return response.status_code
    except requests.ConnectionError:
        return None
    except StandardError:
        return None
    except:
        return None

def grab_domain(url):
    """
    Returns the domain of a URL
    """
    try:
        url = extract(url)
    except Exception:
        raise Exception("This URL doesn't work: \"{0}\"".format(url))
    #concatenate subdomain, domain and tld
    return '.'.join((url[0], url[1], url[2])) if url[0] else '.'.join((url[1], url[2]))

def check_url(capture_record):
    """
    Check if a URL exists without downloading the whole file.
    We only check the URL header.
    """
    # Ensure that the response code is not an error
    # (No 4xx or 5xx errors)
    the_code = get_server_status_code(capture_record.url)
    capture_record.url_response_code = the_code
    
    # If the status code is an error, update the capture_status accordingly
    if the_code is None:
        capture_record.capture_status = 0
        return False
    if the_code < 400 or app.config['CAPTURE_ERRORS'] == True:
        capture_record.capture_status = the_code
        return True
    else:
        capture_record.capture_status = the_code
        return False

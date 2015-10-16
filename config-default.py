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
import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

# Database setup
SQLALCHEMY_DATABASE_URI = os.getenv('sketchy_db', 'sqlite:////tmp/sketchy-db.db')

# Set scheme and hostname:port of your server.
# Alterntively, you can export the 'host' variable on your system to set the
# host and port.
# If you are using Nginx with SSL, change the scheme to https.
BASE_URL = 'http://%s' % os.getenv('host', '127.0.0.1:8000')

# Broker configuration information, currently only supporting Redis
CELERY_BROKER_URL = os.getenv('sketchy_broker_url', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.getenv('sketchy_result_backend', 'redis://localhost:6379')

# Only accept json content for celery
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Local Screenshot storage
LOCAL_STORAGE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')

# Maximum time to wait for PhantomJS to generate a screenshot
PHANTOMJS_TIMEOUT = 35

# Maximum number of Celery Job retries on failure
MAX_RETRIES = 3

# Seconds to sleep before retrying the task
COOLDOWN = 5

# Path to Phanotom JS
PHANTOMJS = '/usr/local/bin/phantomjs'

# S3 Specific configurations
# This will store your sketches, scrapes, and html in an S3 bucket
USE_S3 = os.getenv('use_s3', 'False').lower() == 'true'
S3_BUCKET_PREFIX = os.getenv('bucket_prefix', '')
S3_LINK_EXPIRATION = 6000000
S3_BUCKET_REGION_NAME = os.getenv('bucket_region_name', 'us-east-1')

# Token Auth Setup
REQUIRE_AUTH = os.getenv('require_auth', 'False').lower() == 'true'
AUTH_TOKEN = os.getenv('auth_token', 'test')

# Log file configuration (currently only logs errors)
SKETCHY_LOG_FILE = "sketchy.log"

# Perform SSL host validation (set to False if you want to scrape/screenshot sketchy websites)
SSL_HOST_VALIDATION = False

# Ignore a comma seperated list of IP ranges
# any host that falls within the range will be ignored
IP_BLACKLISTING = os.getenv('ip_blacklisting', 'False').lower() == 'true'
IP_BLACKLISTING_RANGE = os.getenv('ip_blacklisting_range', '10.0.0.1/8,11.0.0.1/24,100.0.0.1/24')

# Enable this option to screenshot webpages that generate 4xx or 5xx HTTP error codes
CAPTURE_ERRORS = True

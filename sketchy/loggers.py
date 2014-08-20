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
from logging import Formatter
from logging.handlers import RotatingFileHandler
from celery.utils.log import logging

def sketchy_logger(app):
# App logger
    file_handler = RotatingFileHandler(
        app.config.get('SKETCHY_LOG_FILE'),
        maxBytes=10000000,
        backupCount=100)
    file_handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

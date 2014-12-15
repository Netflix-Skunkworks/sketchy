#!/usr/bin/env python
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
# Imports
import logging
import os

from functools import wraps
from logging import Formatter
from celery import Celery, Task
from flask.ext.restful import Api
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Resource, reqparse
from flask import Flask, send_from_directory, request, abort
from sqlalchemy.exc import IntegrityError
from sketchy.loggers import sketchy_logger
from logging.handlers import RotatingFileHandler
from werkzeug import secure_filename
# App Config
app = Flask(__name__)
# Specify which config file to load (config-test or config-default)
app.config.from_object('config-default')
db = SQLAlchemy(app)
sketchy_logger(app)

# Model Imports
from sketchy.models.capture import Capture
from sketchy.models.static import Static

def make_celery(app):
    """Make a celery object that extends Flask context."""
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

        def after_return(self, status, retval, task_id, args, kwargs, einfo):
            db.session.remove()

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            from sketchy.controllers.tasks import finisher
            # Check if the failures was on a capture or a static capture
            try:
                if kwargs['model'] == 'capture':
                    the_record = Capture.query.filter(Capture.id == kwargs['capture_id']).first()
                else:
                    the_record = Static.query.filter(Static.id == kwargs['capture_id']).first()
                the_record.job_status = 'FAILURE'
                if str(exc):
                    the_record.capture_status = str(exc)
                app.logger.error(exc)
                db.session.add(the_record)
                db.session.commit()
            except IntegrityError, exc:
                app.logger.error(exc)

            if the_record and the_record.callback:
                finisher(the_record)

    celery.Task = ContextTask
    return celery

# Instantiate celery object for associated tasks
celery = make_celery(app)

def app_key_check(view_function):
    """
    Token auth decorator returns 401 if token is not specified or incorrect
    """
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if app.config['REQUIRE_AUTH'] == True and app.config['AUTH_TOKEN']:
            if request.headers.get('Token') == app.config['AUTH_TOKEN'] or request.args.get('token') == app.config['AUTH_TOKEN']:
                return view_function(*args, **kwargs)
            else:
                app.logger.error("Missing required 'TOKEN'")
                abort(401)
        else:
            return view_function(*args, **kwargs)
    return decorated_function

# If Token Auth is required, apply to Flask API
flask_api = Api(app, decorators=[app_key_check])

# Setup API calls for sketching urls or html files
from controllers.controller import CaptureView, CaptureViewList, CaptureViewLast, Eager
from controllers.static_upload import StaticView, StaticViewList, StaticViewLast
flask_api.add_resource(CaptureView, '/api/v1.0/capture/<int:id>')
flask_api.add_resource(CaptureViewList, '/api/v1.0/capture')
flask_api.add_resource(CaptureViewLast, '/api/v1.0/capture/last')
flask_api.add_resource(Eager, '/eager')
flask_api.add_resource(StaticView, '/api/v1.0/static/<int:id>')
flask_api.add_resource(StaticViewList, '/api/v1.0/static')
flask_api.add_resource(StaticViewLast, '/api/v1.0/static/last')

# Setup Screenshot directory
if not os.path.exists(app.config['LOCAL_STORAGE_FOLDER']):
    os.makedirs(app.config['LOCAL_STORAGE_FOLDER'])


@app.route('/files/<filename>')
@app_key_check
def uploaded_file(filename):
    """
    Route to retrieve a sketch, scrape, or html file when requested.
    If token auth is required, run the app_key_check decorator.
    """
    return send_from_directory(app.config['LOCAL_STORAGE_FOLDER'],
                               filename, as_attachment=True)
                               
# Healthcheck 
@app.route('/healthcheck')
def home():
    return 'Ok'
    
# Launch.
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT)

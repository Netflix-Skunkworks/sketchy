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
import json
import uuid
import werkzeug
import os

from sketchy import db, app
from sketchy.models.static import Static
from flask import jsonify
from flask.ext.restful import Resource, reqparse
from sqlalchemy.exc import IntegrityError
from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage


class StaticView(Resource):
    """
    API Provides CRUD operations for Static Captures based on id.

    Methods:
    GET
    """
    def get(self, id):
        """
        Retrieve Captures based on id
        """
        static_record = Static.query.filter(Static.id == id).first()
        if static_record is not None:
            return static_record.as_dict()
        else:
            return 'No static capture found!', 404

class StaticViewLast(Resource):
    """
    API Provides last static capture in database.

    Methods:
    GET
    """
    def get(self):
        """
        Retrieve Static based on id
        """
        static_record = Static.query.order_by('-id').first()

        if static_record is not None:
            return static_record.as_dict()
        else:
            return 'No static record found!', 404

class StaticViewList(Resource):
    """
    API Provides CRUD operations for Sstatic HTML file captures.

    Methods:
    GET
    POST
    """
    def allowed_extension(self,filename):
        """
        Check if the provided file has an html or htm file extension.
        """
        ALLOWED_EXTENSIONS = ['html', 'htm']
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    def is_allowed_file(self,f):
        """
        Ensure file is secure, is allowed, and generate a uniqe filename.
        """
        if self.allowed_extension(f.filename):
            filename = secure_filename(f.filename)
            filename = str(uuid.uuid4()) + '-' + filename
        else:
            raise ValueError('not a valid file')
        return filename

    def get(self):
        """
        Retrieve all static records the database
        """
        results = []
        for row in Static.query.order_by(Static.id.desc()).all():
            results.append(row.as_dict())

        return results

    def post(self):
        """
        Create a new Static Capture

        User must provide html file in multipart upload
        """
        parser = reqparse.RequestParser()
        parser.add_argument('file',
                        type=werkzeug.datastructures.FileStorage,
                        required=True,
                        location='files')
        parser.add_argument('callback', type=str, location='form')
        args = parser.parse_args()
        file_object = args['file']
        # User can provide optional callback field for static record
        callback = args['callback']

        # Validation is going down here
        try:
            the_filename = self.is_allowed_file(file_object)
        except Exception as err:
            return err.message, 403

        # Instantiate a new static model record
        static_record = Static()
        static_record.filename = str(the_filename)

        if callback:
            static_record.callback = str(callback)
        # Add the static_record and commit to the DB
        try:
            db.session.add(static_record)
            db.session.commit()
        except IntegrityError, exc:
            return {"error": exc.message}, 500

        # Refresh static_record to obtain an ID for record
        db.session.refresh(static_record)

        # Write uploaded HTML file to local storage disk
        try:
            new_html_file = open(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], the_filename), 'w+')
            file_object.save(new_html_file)
            new_html_file.close()
        except Exception as err:
            return str(err.message), 500

        # Set the base_url for retrieving the static records
        base_url = app.config['BASE_URL']

        # Execute the celery static capture task to retrieve static text scrape and screenshot
        celery_sketch = tasks.celery_static_capture.delay(base_url, capture_id=static_record.id, model='static')
                     
        return static_record.as_dict(), 201

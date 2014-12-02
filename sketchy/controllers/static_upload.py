import tasks

from sketchy import db, app
from sketchy.models.static import Static
import json
import uuid
from flask import jsonify
from flask.ext.restful import Resource, reqparse
from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage
import werkzeug
from sqlalchemy.exc import IntegrityError
import os
# parser = reqparse.RequestParser()
# parser.add_argument('name', type=werkzeug.datastructures.FileStorage, location='files')

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




class StaticViewList(Resource):
    """
    API Provides CRUD operations for Capturees.

    Methods:
    GET
    POST
    """
    def allowed_extension(self,filename):
        ALLOWED_EXTENSIONS = ['html', 'htm', 'txt', 'js', 'css']
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    def is_allowed_file(self,f):

        if self.allowed_extension(f.filename):
            filename = secure_filename(f.filename)
            filename = str(uuid.uuid4()) + '-' + filename
        else:
            raise ValueError('not a valid file')
        return filename

    def get(self):
        """
        Retrieve all sketch records the database
        """
        results = []
        for row in Static.query.order_by(Static.id.desc()).all():
            results.append(row.as_dict())

        return results

    def post(self):

        parser = reqparse.RequestParser()
        parser.add_argument('file',
                        type=werkzeug.datastructures.FileStorage,
                        required=True,
                        location='files')
        parser.add_argument('text', type=str, location='form')
        args = parser.parse_args()
        file_object = args['file']
        callback = args['text']

        # Validation is going down here
        try:
            the_filename = self.is_allowed_file(file_object)
            # if len(file_object.stream.read()) < 1:
            #     raise ValueError("File size should be greater than 1")
        except Exception as err:
            return err.message, 403

        static_record = Static()
        static_record.filename = str(the_filename)

        if callback:
            static_record.callback = str(callback)
        # # Add the capture_record and commit to the DB
        try:
            db.session.add(static_record)
            db.session.commit()
        except IntegrityError, exc:
            return {"error": exc.message}, 500

        # Refresh capture_record to obtain an ID for record
        db.session.refresh(static_record)

        try:
            new_html_file = open(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], the_filename), 'w+')
            file_object.save(new_html_file)
            new_html_file.close()
        except Exception as err:
            return str(err.message), 500

        base_url = app.config['BASE_URL']

        celery_sketch = tasks.celery_static_capture.delay(base_url, capture_id=static_record.id, model='static')
                     
        return static_record.as_dict(), 201

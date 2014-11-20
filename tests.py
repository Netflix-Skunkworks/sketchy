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
import sys

sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

import json
import unittest
from sketchy import app, db
from sketchy.controllers import tasks

class Sketch(unittest.TestCase):
    app.config.from_object('config-test')

    def setUp(self):
        self.test_app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


    def check_content_type(self, headers):
        self.assertEquals(headers['Content-Type'], 'application/json')

    def eager_get(self, endpoint):
        rv = self.test_app.get(endpoint, content_type='text/html')
        print str(rv.data)

        return (rv.status_code, rv.data, rv.headers)

    def token_get(self, endpoint):
        rv = self.test_app.get(endpoint, content_type='text/html', headers=[('Token', 'test')])
        print str(rv.data)

        return (rv.status_code, rv.data, rv.headers)
    def get(self, endpoint):
        rv = self.test_app.get(endpoint, content_type='application/json')
        self.check_content_type(rv.headers)
        return (rv.status_code, json.loads(rv.data))

    def post(self, endpoint, data):
        rv = self.test_app.post(endpoint, data=json.dumps(data), content_type='application/json')
        self.check_content_type(rv.headers)
        return (rv.status_code, json.loads(rv.data))

class SketchApiTestCase(Sketch):
    """Class of unit tests"""
    _multiprocess_shared_ = True


    def test_without_json_body(self):
        blob = {}
        code, data = self.post('/api/v1.0/capture', blob)

        self.assertEquals(code, 400)


    def test_eager_sketch(self):
        code, data, headers = self.eager_get('/eager?url=http://google.com&type=sketch')

        self.assertEquals(code, 200)
        self.assertEquals(headers['Content-Disposition'], "attachment; filename=google.com_1.png")


    def test_eager_scrape(self):
        code, data, headers = self.eager_get('/eager?url=http://google.com&type=scrape')

        self.assertEquals(code, 200)
        self.assertEquals(headers['Content-Disposition'], "attachment; filename=google.com_1.txt")


    def test_eager_html(self):
        code, data, headers = self.eager_get('/eager?url=http://google.com&type=html')

        self.assertEquals(code, 200)
        self.assertEquals(headers['Content-Disposition'], "attachment; filename=google.com_1.html")


    def test_eager_invalid(self):
        code, data, headers = self.eager_get('/eager?url=http://google.com&type=')

        self.assertEquals(code, 406)


    def test_celery_sketch(self):
        from sketchy.models.capture import Capture
        capture_record = Capture()
        capture_record.url = 'http://xkcd.com'
        db.session.add(capture_record)
        db.session.commit()
        db.session.refresh(capture_record)

        app.config.update(USE_S3=False)
        files_to_write = tasks.do_capture(200, capture_record, "http://127.0.0.1:7001")
        self.assertEquals(files_to_write['html'], 'xkcd.com_1.html')
        self.assertEquals(files_to_write['sketch'], 'xkcd.com_1.png')
        self.assertEquals(files_to_write['scrape'], 'xkcd.com_1.txt')

        try:
            os.remove(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], 'xkcd.com_1.html'))
            os.remove(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], 'xkcd.com_1.png'))
            os.remove(os.path.join(app.config['LOCAL_STORAGE_FOLDER'], 'xkcd.com_1.txt'))
        except:
            pass

    def test_check_url_valid(self):
       from sketchy.models.capture import Capture
       capture_record = Capture()
       capture_record.url = 'http://xkcd.com'
       db.session.add(capture_record)
       db.session.commit()
       db.session.refresh(capture_record)

       rst = tasks.check_url.delay(capture_id=capture_record.id).get()
       self.assertEquals(rst, '200')

    def test_token_valid(self):
        app.config.update(REQUIRE_AUTH=True, AUTH_TOKEN='test')
        code, data, headers = self.token_get('/api/v1.0/capture')
        app.config.update(REQUIRE_AUTH=False, AUTH_TOKEN='test')
        self.assertEquals(code, 200)

    def test_token_invalid(self):
        app.config.update(REQUIRE_AUTH=True, AUTH_TOKEN='not_the_right_token')
        code, data, headers = self.token_get('/api/v1.0/capture')
        app.config.update(REQUIRE_AUTH=False, AUTH_TOKEN='test')
        self.assertEquals(code, 401)

    def test_check_url_invalid(self):
        from sketchy.models.capture import Capture
        capture_record = Capture()
        capture_record.url = 'http://redditsss.com'
        db.session.add(capture_record)
        db.session.commit()
        db.session.refresh(capture_record)
        print capture_record.id
        try:
            rst = tasks.check_url.delay(capture_id=capture_record.id).get()
        except Exception as err:
            self.assertEquals(str(err.message), 'None: Max retries exceeded with url: / (Caused by redirect)')

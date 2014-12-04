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
import datetime

from sketchy import db

def _get_date():
    """Returns the current date when called"""
    return datetime.datetime.now()

class Capture(db.Model):
    """
    Capture database model

    """
    __tablename__ = 'Capture'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), unique=False, nullable=False)
    job_status = db.Column(db.String(512), unique=False)
    capture_status = db.Column(db.String(512), unique=False)
    created_at = db.Column(db.DateTime, default=_get_date, unique=False)
    modified_at = db.Column(db.DateTime, onupdate=_get_date, unique=False)
    sketch_url = db.Column(db.String(1500), unique=False)
    scrape_url = db.Column(db.String(1500), unique=False)
    html_url = db.Column(db.String(1500), unique=False)
    status_only = db.Column(db.Boolean)
    callback = db.Column(db.String(512))
    retry = db.Column(db.Integer)
    url_response_code = db.Column(db.Integer, unique=False)

    def __init__(self):
        self.job_status = 'CREATED'

    def as_dict(self):
        """Return Capture model as a JSON object"""
        sketch_dict = {}

        sketch_dict['id'] = self.id
        sketch_dict['url'] = self.url
        if self.status_only is not None: 
            sketch_dict['status_only'] = self.status_only
        if self.callback is not None: 
            sketch_dict['callback'] = self.callback
        sketch_dict['capture_status'] = self.capture_status
        sketch_dict['job_status'] = self.job_status
        sketch_dict['created_at'] = str(self.created_at)
        sketch_dict['retry'] = self.retry
        sketch_dict['modified_at'] = str(self.modified_at)
        sketch_dict['sketch_url'] = self.sketch_url
        sketch_dict['scrape_url'] = self.scrape_url
        sketch_dict['html_url'] = self.html_url
        sketch_dict['url_response_code'] = self.url_response_code
        return sketch_dict

    def __repr__(self):
        """Return the url of the object"""
        return '<Url %r' % self.url

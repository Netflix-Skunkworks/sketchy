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
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='sketchy',
    version='1.1',
    long_description=read('README.md'),
    packages=['sketchy'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
            'Flask==0.10.1',
            'Flask-SQLAlchemy==1.0',
            'MySQL-python==1.2.5',
            'Flask-Script==2.0.5',
            'SQLAlchemy==0.9.7',
            'Flask-RESTful==0.2.12',
            'requests==2.3.0',
            'gunicorn==19.1.0',
            'tldextract==1.4',
            'supervisor==3.1.0',
            'celery==3.1.13',
            'boto==2.32.1',
            'redis==2.10.1',
            'lxml==3.3.5',
            'subprocess32==3.2.6'
        ]
)

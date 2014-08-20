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
from sketchy import app, db
from flask_script import Command, Option
from gunicorn.app.base import Application
from flask.ext.script import Manager, Server
from flask_script.commands import ShowUrls, Clean

manager = Manager(app)
server = Server(host="0.0.0.0", port=7001)
manager.add_command("runserver", server)
app.config.from_object('config-default')

@manager.shell
def make_shell_context():
    """
    Creates a python REPL with several default imports
    in the context of the app
    """
    return dict(app=app)

@manager.command
def create_db():
    """
    Creates a database with all of the tables defined in
    your Alchemy models
    """
    db.create_all()

@manager.command
def clear():
    """
    Remove all local files
    """
    import shutil
    shutil.rmtree(app.config['LOCAL_STORAGE_FOLDER']) 

@manager.command
def drop_db():
    """
    Drops a database with all of the tables defined in
    your Alchemy models
    """
    db.drop_all()

class Start(Command):

    description = 'Run the app within Gunicorn'

    def __init__(self, host='127.0.0.1', port=8000, workers=4):

        self.port = port
        self.host = host
        self.workers = workers


    def get_options(self):
        return (
            Option('-t', '--host',
                   dest='host',
                   default=self.host),

            Option('-p', '--port',
                   dest='port',
                   type=int,
                   default=self.port),
            
            Option('-w', '--workers',
                   dest='workers',
                   type=int,
                   default=self.workers)
        )

    def handle(self, app, *args, **kwargs):

        host = kwargs['host']
        port = kwargs['port']
        workers = kwargs['workers']

        def remove_non_gunicorn_command_line_args():
            import sys
            args_to_remove = ['--port','-p']
            def args_filter(name_or_value):
                keep = not args_to_remove.count(name_or_value)
                if keep:
                    previous = sys.argv[sys.argv.index(name_or_value) - 1]
                    keep = not args_to_remove.count(previous)
                return keep
            sys.argv = filter(args_filter, sys.argv)

        remove_non_gunicorn_command_line_args()

        from gunicorn import version_info
        if version_info < (0, 9, 0):
            from gunicorn.arbiter import Arbiter
            from gunicorn.config import Config
            print Config({'bind': "%s:%d" % (host, int(port)),'workers': workers})
            arbiter = Arbiter(Config({'bind': "%s:%d" % (host, int(port)),'workers': workers}), app)
            arbiter.run()
        else:
            class FlaskApplication(Application):
                def init(self, parser, opts, args):
                    return {
                        'bind': '{0}:{1}'.format(host, port),
                        'workers': workers
                    }

                def load(self):
                    return app

            FlaskApplication().run()

@manager.command
def list_routes():
    output = []
    func_list = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = app.view_functions[rule.endpoint].__doc__

    from pprint import pprint
    pprint(func_list)

if __name__ == "__main__":
    manager.add_command("clean", Clean())
    manager.add_command("start", Start())
    manager.add_command("show_urls", ShowUrls())

    manager.run()

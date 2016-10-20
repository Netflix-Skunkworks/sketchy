![Sketchy](http://i.imgur.com/WvGJ8Ri.jpg)
#Overview#
## What is Sketchy?

Sketchy is a task based API for taking screenshots and scraping text from websites.

## What is the Output of Sketchy?

Sketchy's capture model contains all of the information associated with screenshotting, scraping, and storing html files from a provided URL. Screenshots (sketches), text scrapes, and html files can either be stored locally or on an S3 bucket. Optionally, token auth can be configured for creating and retrieving captures. Sketchy can also perform callbacks if required.

## How Does Sketchy Do It?

Sketchy utilizes PhantomJS with [lazy-rendering](https://github.com/kimmobrunfeldt/url-to-image) to ensure Ajax heavy sites are captured correctly. Sketchy also utilizes [Celery](http://www.celeryproject.org/) task management system allowing users to scale Sketchy accordingly and manage time intensive captures.

## Release History ##

**Version 1.1.2** - *January 27, 2016*

This minor release addresses a bug and a new configuration option:

- A default timeout of 5 seconds was added to check_url task.  This should prevent workers from hanging [#26](https://github.com/Netflix/sketchy/issues/26).
- You can now specify a cookie store via an environment variable 'phantomjs_cookies' which will be used by PhantomJS.  This env variable simply needs to be a string of key/value cookie pairs.

**Version 1.1.1** - *June 16, 2015*

This minor release addresses a few bugs and some new configuration features:

- A new configuration option `PHANTOMJS_TIMEOUT` allows setting how long to wait for a capture to render before terminating the subprocess
- Celery retry functionality was added when PhantomJS fails to render a screenshot before the PhantomJS timeout occurs
- An incremental PhantomJS timeout was introduced to improve PhantomJS success at generating very large screenshots.  Each time PhantomJS retries to render a screenshot 5 seconds will be added to the previous `PHANTOMJS_TIMEOUT` configuration option.
- A number of typos have been fixed and comments have been added.

**Version 1.1** - *December 4, 2014*

A number of improvements and bug fixes have been made:

- A new model and API endpoint called "Static" was created.  This allows users to send Sketchy a static HTML file for text scraping and screenshoting.  See the [Wiki](https://github.com/Netflix/Sketchy/wiki) for usage information.
- New PhantomJS script called 'static.js' for creating screenshots of static html files.
- Creation of a new endpoint: api/v1.0/capture/last which shows the last capture that was taken.
- Creation of a new endpoint: api/v1.0/static/last which shows the last static capture that was taken.
- API list view is now reverse sorted so most recent capture is listed on the top of the page.
- For callback requests, capture status is now updated
- Task retry has been optimized to only retry on ConnectionErrors.  This should speedup errors that would never succeed during a retry.
- A new configuration setting "SSL\_HOST\_VALIDATION" can be set to scrape/screenshot webpages with SSL errors.
- A new configuration setting "CAPTURE_ERRORS" can be used to scrape/screenshot webpages that have 4xx or 5xx http status codes.

#Documentation#

Documentation is maintained in the Github [Wiki](https://github.com/Netflix/Sketchy/wiki)

#Docker#
Sketchy is also available as a [Docker](https://github.com/sbehrens/docker_sketchy) container.

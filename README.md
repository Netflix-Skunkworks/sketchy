![Sketchy](http://i.imgur.com/WvGJ8Ri.jpg)
#Overview#
## What is Sketchy?

Sketchy is a task based API for taking screenshots and scraping text from websites. 

## What is the Output of Sketchy?

Sketchy's capture model contains all of the information associated with screenshotting, scraping, and storing html files from a provided URL. Screenshots (sketches), text scrapes, and html files can either be stored locally or on an S3 bucket. Optionally, token auth can be configured for creating and retrieving captures. Sketchy can also perform callbacks if required.

## How Does Sketchy Do It?

Sketchy utilizes PhantomJS with [lazy-rendering](https://github.com/kimmobrunfeldt/url-to-image) to ensure Ajax heavy sites are captured correctly. Sketchy also utilizes [Celery](http://www.celeryproject.org/) task management system allowing users to scale Sketchy accordingly and manage time intensive captures.

## Release History ##

**Version 1.1** - *December 4, 2014*

A number of improvements and bug fixes have been made:

- A new model and API endpoint called "Static" was created.  This allows users to send Sketchy a static HTML file for text scraping and screenshoting.  See the [Wiki](https://github.com/Netflix/Sketchy/wiki) for usage information.  
- New PhantomJS script called 'static.js' for creating screenshots of static html files.  
- Creation of a new endpont: api/v1.0/capture/last which shows the last capture that was taken.  
- Creation of a new endpont: api/v1.0/static/last which shows the last static capture that was taken.  
- API list view is now reverse sorted so most recent capture is listed on the top of the page.
- For callback requests, capture status is now updated
- Task retry has been optimitzed to only retry on ConnectionErrors.  This should speedup errors that would never succeed during a retry.
- A new configuration setting "SSL\_HOST\_VALIDATION" can be set to scrape/screenshot webpages with SSL errors.
- A new configuration setting "CAPTURE_ERRORS" can be used to scrape/screenshot webpages that have 4xx or 5xx http status codes.

#Documentation#

Documentation is maintained in the Github [Wiki](https://github.com/Netflix/Sketchy/wiki)

#Docker#
Sketchy is also available as a [Docker](https://github.com/sbehrens/docker_sketchy) container.  

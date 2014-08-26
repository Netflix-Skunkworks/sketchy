![Sketchy](http://i.imgur.com/WvGJ8Ri.jpg)
#Overview#
## What is Sketchy?

Sketchy is a task based API for taking screenshots and scraping text from websites. 

## What is the Output of Sketchy?

Sketchy's capture model contains all of the information associated with screenshotting, scraping, and storing html files from a provided URL. Screenshots (sketches), text scrapes, and html files can either be stored locally or on an S3 bucket. Optionally, token auth can be configured for creating and retrieving captures. Sketchy can also perform callbacks if required.

## How Does Sketchy Do It?

Sketchy utilizes PhantomJS with [lazy-rendering](https://github.com/kimmobrunfeldt/url-to-image) to ensure Ajax heavy sites are captured correctly. Sketchy also utilizes [Celery](http://www.celeryproject.org/) task management system allowing users to scale Sketchy accordingly and manage time intensive captures.

#Documentation#

Documentation is maintained in the Github [Wiki](https://github.com/Netflix/Sketchy/wiki)

#Docker#
Sketchy is also available as a [Docker](https://github.com/sbehrens/docker_sketchy) container.  

FROM ubuntu:14.04

WORKDIR /app

RUN apt-get update -y &&\
    apt-get -y -q install python-software-properties software-properties-common wget &&\
    apt-get install -y python-pip python-dev python-psycopg2 libpq-dev nginx supervisor git curl &&\
    apt-get -y install libmysqlclient-dev libxslt-dev libxml2-dev libfontconfig1 &&\
    wget -O /usr/local/share/phantomjs-1.9.7-linux-x86_64.tar.bz2 https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2 &&\
        tar -xf /usr/local/share/phantomjs-1.9.7-linux-x86_64.tar.bz2 -C /usr/local/share/ &&\
        ln -s /usr/local/share/phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs

EXPOSE 8000

ADD . /app/
RUN pip install .


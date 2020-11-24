FROM ubuntu:18.04

WORKDIR /app

ENV OSMOSIS_VERSION=0.48.2

RUN apt-get -y update \
  && apt-get -y install openjdk-8-jre python3-pip curl

RUN set -x \
  && mkdir -p /opt/osmosis \
  && cd /opt/osmosis \
  && curl -L -o osmosis-$OSMOSIS_VERSION.tgz "https://github.com/openstreetmap/osmosis/releases/download/$OSMOSIS_VERSION/osmosis-$OSMOSIS_VERSION.tgz" \
  && tar -xzvf osmosis-$OSMOSIS_VERSION.tgz \
  && rm -f osmosis-$OSMOSIS_VERSION.tgz \
  && ln -s /opt/osmosis/bin/osmosis /usr/local/bin/osmosis

COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./start.py .
RUN chmod u+x /app/start.py
CMD ./start.py

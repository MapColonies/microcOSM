FROM openjdk:latest

MAINTAINER Daniel Hermon <cl_danielhermon@rnd-hub.com>

ENV OSMOSIS_VERSION=0.48.2

RUN set -x \
  && useradd -ms /bin/bash osmosis \
  && mkdir -p /opt/osmosis \
  && cd /opt/osmosis \
  && curl -L -o osmosis-$OSMOSIS_VERSION.tgz "https://github.com/openstreetmap/osmosis/releases/download/$OSMOSIS_VERSION/osmosis-$OSMOSIS_VERSION.tgz" \
  && tar -xzvf osmosis-$OSMOSIS_VERSION.tgz \
  && rm -f osmosis-$OSMOSIS_VERSION.tgz \
  && ln -s /opt/osmosis/bin/osmosis /usr/local/bin/osmosis

USER osmosis
CMD ["osmosis"]

FROM ubuntu:20.04

ENV IMPOSM_VERSION=0.11.0

RUN apt-get -y update
RUN apt-get install -y \
  curl \
  libpq-dev \
  python3-pip

RUN set -x \
  && mkdir -p /opt/imposm \
  && cd /opt/imposm \
  && curl -L -o imposm-$IMPOSM_VERSION.tar.gz "https://github.com/omniscale/imposm3/releases/download/v$IMPOSM_VERSION/imposm-$IMPOSM_VERSION-linux-x86-64.tar.gz" \
  && tar -xzvf imposm-$IMPOSM_VERSION.tar.gz \
  && rm -f imposm-$IMPOSM_VERSION.tar.gz \
  && ln -s /opt/imposm/imposm-$IMPOSM_VERSION-linux-x86-64/imposm /usr/local/bin/imposm

COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

RUN mkdir /var/log/osm-seed

ENV IMPOSMDATA /mnt/data
RUN mkdir -p "$IMPOSMDATA" && chmod 777 "$IMPOSMDATA"
VOLUME /mnt/data

WORKDIR /osm
COPY ./config/${IMPOSM_MAPPING_FILE} ${IMPOSM_MAPPING_FILE}
COPY ./config/postgis_helpers.sql postgis_helpers.sql
COPY ./config/postgis_index.sql postgis_index.sql
COPY ./config/first-osm-import.pbf .
COPY start.py start.py
RUN chmod a+x start.py
CMD ./start.py

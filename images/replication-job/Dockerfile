FROM ubuntu:18.04
RUN apt-get update && apt-get install -y \
    python-pip \
    libz-dev zlib1g-dev \
    curl unzip \
    tar \
    bzip2 default-jre
RUN pip install awscli
# Install osmosis
WORKDIR /osmosis
ENV OSMOSIS_VERSION=0.48.2
RUN set -x \
    && useradd -ms /bin/bash osmosis \
    && mkdir -p /opt/osmosis \
    && cd /opt/osmosis \
    && curl -L -o osmosis-$OSMOSIS_VERSION.tgz "https://github.com/openstreetmap/osmosis/releases/download/$OSMOSIS_VERSION/osmosis-$OSMOSIS_VERSION.tgz" \
    && tar -xzvf osmosis-$OSMOSIS_VERSION.tgz \
    && rm -f osmosis-$OSMOSIS_VERSION.tgz \
    && ln -s /opt/osmosis/bin/osmosis /usr/local/bin/osmosis
WORKDIR /app
RUN mkdir data
VOLUME ["/app/data"]
COPY ./start.sh .
CMD ./start.sh

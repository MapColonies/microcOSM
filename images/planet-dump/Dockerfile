FROM ubuntu:18.04
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ="Asia/Jerusalem"
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    python-pip \
    software-properties-common \
    libz-dev zlib1g-dev \
    curl unzip \
    gdal-bin tar \
    bzip2 clang git \
    default-jre default-jdk gradle
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
WORKDIR  /app
COPY ./start.sh .
CMD ./start.sh

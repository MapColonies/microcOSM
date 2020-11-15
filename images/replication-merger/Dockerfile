FROM ubuntu:18.04
ENV OSMOSIS_VERSION=0.48.2
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    python-pip \
    python3-pip \
    software-properties-common \
    libz-dev zlib1g-dev \
    curl unzip \
    gdal-bin tar \
    bzip2 clang git \
    default-jre default-jdk gradle
RUN set -x \
  && useradd -ms /bin/bash osmosis \
  && mkdir -p /opt/osmosis \
  && cd /opt/osmosis \
  && curl -L -o osmosis-$OSMOSIS_VERSION.tgz "https://github.com/openstreetmap/osmosis/releases/download/$OSMOSIS_VERSION/osmosis-$OSMOSIS_VERSION.tgz" \
  && tar -xzvf osmosis-$OSMOSIS_VERSION.tgz \
  && rm -f osmosis-$OSMOSIS_VERSION.tgz \
  && ln -s /opt/osmosis/bin/osmosis /usr/local/bin/osmosis
WORKDIR /app
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
COPY ./start.py .
CMD ["-u", "./start.py"]
ENTRYPOINT [ "python3" ]

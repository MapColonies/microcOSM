FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libz-dev zlib1g-dev \
    curl \
    tar \
    bzip2 openjdk-8-jre \
    python3-pip

# Install osmosis
ENV OSMOSIS_VERSION=0.48.2
RUN set -x \
    && useradd -ms /bin/bash osmosis \
    && mkdir -p /opt/osmosis \
    && cd /opt/osmosis \
    && curl -L -o osmosis-$OSMOSIS_VERSION.tgz "https://github.com/openstreetmap/osmosis/releases/download/$OSMOSIS_VERSION/osmosis-$OSMOSIS_VERSION.tgz" \
    && tar -xzvf osmosis-$OSMOSIS_VERSION.tgz \
    && rm -f osmosis-$OSMOSIS_VERSION.tgz \
    && ln -s /opt/osmosis/bin/osmosis /usr/local/bin/osmosis

# configure startup script
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY start.py .
ENTRYPOINT ["python3"]
CMD ["-u", "./start.py"]

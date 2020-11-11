FROM ubuntu:18.04

RUN apt-get -y update && \
  apt-get install -y software-properties-common \
  postgresql-client curl unzip


# Gdal is required to process the natural earth files
RUN add-apt-repository ppa:ubuntugis/ppa && \
  apt-get -y update && \
  apt-get install -y gdal-bin

COPY scripts scripts
COPY start.sh start.sh
RUN chmod a+x start.sh
CMD ./start.sh
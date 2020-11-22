FROM ubuntu:18.04

WORKDIR /app

RUN apt-get -y update && \
  apt-get install -y \
  libpq-dev \
  gdal-bin \ 
  python3-pip

RUN mkdir /var/log/osm-seed

COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./script/get-external-data.py /usr/bin/.
COPY ./config/external-data.yaml .
COPY ./start.py .
RUN chmod u+x /app/start.py && chmod u+x /usr/bin/get-external-data.py
CMD ./start.py
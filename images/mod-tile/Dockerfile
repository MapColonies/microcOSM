FROM ubuntu:18.04
RUN apt-get -y update && apt-get -y install software-properties-common \
  # fonts
  fonts-noto-cjk \
  fonts-noto-hinted \
  fonts-noto-unhinted \
  ttf-unifont
RUN add-apt-repository multiverse && apt update && apt -y install libboost-all-dev \
  git-core \
  tar \
  unzip \
  wget \
  bzip2 \
  build-essential \
  autoconf \
  libtool \
  libxml2-dev \
  libgeos-dev \
  libgeos++-dev \
  libpq-dev \
  libbz2-dev \
  libproj-dev \
  munin-node \
  munin \
  libprotobuf-c0-dev \
  protobuf-c-compiler \
  libfreetype6-dev \
  libtiff5-dev \
  libicu-dev \
  libgdal-dev \
  libcairo-dev \
  libcairomm-1.0-dev \
  apache2 \
  apache2-dev \
  libagg-dev \
  liblua5.2-dev \
  ttf-unifont \
  lua5.1 \
  liblua5.1-dev \
  libgeotiff-epsg \
  python3-pip \
  # mapnik
  gdal-bin \
  libmapnik-dev \
  mapnik-utils \
  python-mapnik
ENV workdir=/src
WORKDIR $workdir
# mod_tile
RUN git clone -b 0.5 git://github.com/openstreetmap/mod_tile.git && \
  cd mod_tile && \
  ./autogen.sh && \
  ./configure && \
  make && \
  make install && \
  make \
  install-mod_tile && \
  ldconfig
# osm-carto dependencies
RUN apt-get -y install nodejs-dev \
  node-gyp \
  libssl1.0-dev
# carto & osm-carto
RUN git clone git://github.com/gravitystorm/openstreetmap-carto.git && \
  cd openstreetmap-carto && \
  apt -y install npm nodejs && \
  npm install -g carto
COPY ./config/project.mml ./openstreetmap-carto/project.mml
# configure apache2, mod_tile & renderd
COPY ./config/renderd.conf /usr/local/etc/renderd.conf
RUN mkdir -p /var/lib/mod_tile && mkdir -p /var/run/renderd
COPY ./config/mod_tile.conf /etc/apache2/conf-available/mod_tile.conf
RUN a2enconf mod_tile
COPY ./config/apache2.conf /etc/apache2/sites-available/000-default.conf
# configure startup script
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY start.py .
ENTRYPOINT ["python3"]
CMD ["-u", "./start.py"]
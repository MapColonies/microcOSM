FROM ubuntu:bionic as base

ARG APP_NAME=core/osm-web
ARG BUILD_DATE
ARG SERVER_URL=localhost
ARG PORT=3000
ARG VERSION
ARG DEBIAN_FRONTEND=noninteractive

ENV RAILS_ENV=development
ENV SERVER_URL=${SERVER_URL}
ENV TZ="Asia/Jerusalem"
ENV WORKDIR=/openstreetmap-website
ENV POSTGRES_HOST=localhost POSTGRES_DB=osm POSTGRES_USER=postgres

LABEL maintainer="Vitali Ginzburg" \
    org.label-schema.build-date=$BUILD_DATE \
    org.label-schema.name=${APP_NAME} \
    org.label-schema.description="openstreetmap-website (the rails port) development env" \
    org.label-schema.version=$VERSION \
    org.label-schema.schema-version="1.0" \
    org.label-schema.docker.cmd="docker run -d --rm --network some-network -u postgres -p ${PORT}:${PORT} --name ${APP_NAME} ${APP_NAME}:v1" \
    org.label-schema.docker.params="RAILS_ENV=production or development, \
    SERVER_URL=openstreetmap-website url (i.e. openstreetmap.example.com), \
    POSTGRES_HOST=postgres host, \
    POSTGRES_DB=postgres db, \
    POSTGRES_USER=postgres user, \
    POSTGRES_PASSWORD=postgres password"

RUN apt-get update && apt-get install -y ruby2.5 libruby2.5 ruby2.5-dev bundler \
    libmagickwand-dev libxml2-dev libxslt1-dev nodejs \
    apache2 apache2-dev build-essential git-core firefox-geckodriver \
    postgresql postgresql-contrib libpq-dev libsasl2-dev \
    imagemagick libffi-dev libgd-dev libarchive-dev libbz2-dev && \
    gem2.5 install bundler && \
    git clone --depth=1 https://github.com/openstreetmap/openstreetmap-website.git

# Project directory
WORKDIR ${WORKDIR}
COPY config/ config/

RUN rm Gemfile.lock && \
    bundle install && \
    curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - && \
    sudo apt-get install -y nodejs

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list && \
    sudo apt-get update && sudo apt install -y yarn vim && \
    bundle exec rake yarn:install

EXPOSE ${PORT}
COPY start.sh start.sh
# CMD ${WORKDIR}/start.sh
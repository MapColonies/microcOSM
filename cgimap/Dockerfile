FROM ubuntu:20.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && \
    apt-get install -y git ca-certificates gcc g++ make autoconf automake libtool \
       libfcgi-dev libxml2-dev libmemcached-dev \
       libboost-program-options-dev libboost-system-dev \
       libboost-filesystem-dev libboost-locale-dev libcrypto++-dev libyajl-dev \
       libpqxx-dev zlib1g-dev \
       postgresql-12 postgresql-server-dev-all \
       --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the main application.
RUN git clone --depth 1 --branch v0.8.3 https://github.com/zerebubuth/openstreetmap-cgimap.git .

# Compile, install and remove source
RUN ./autogen.sh && \
    ./configure --enable-static --disable-shared --enable-yajl && \
    make && \
    make check && \
    strip openstreetmap-cgimap

FROM ubuntu:20.04

RUN apt-get update -qq && \
    apt-get install -y \
       libfcgi-bin libmemcached11 libboost-locale1.71.0 libboost-program-options1.71.0 \
       libxml2 libcrypto++6 libyajl2 libpqxx-6.4 zlib1g \
       --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/openstreetmap-cgimap /usr/local/bin

WORKDIR /app

COPY ./start.sh /app/start.sh

RUN chgrp root /app/start.sh && chmod g+x ./start.sh && \
    mkdir /.postgresql && chmod g+w /.postgresql

RUN useradd -ms /bin/bash cgimap && usermod -a -G root cgimap

USER cgimap

ENV CGIMAP_PIDFILE /dev/null
ENV CGIMAP_LOGFILE /dev/stdout

EXPOSE 8000

CMD ["/app/start.sh"]
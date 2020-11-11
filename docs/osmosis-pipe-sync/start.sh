#!/bin/bash

osmosis \
--read-apidb host=$MASTER_DB_HOST:$MASTER_DB_PORT database=$MASTER_DATABASE user=$MASTER_DB_USER password=$MASTER_DB_PASSWORD validateSchemaVersion=false outPipe.0=1 \
--read-apidb host=$SLAVE_DB_HOST:$SLAVE_DB_PORT database=$SLAVE_DATABASE user=$SLAVE_DB_USER password=$SLAVE_DB_PASSWORD validateSchemaVersion=false outPipe.0=2 \
--sort type=TypeThenId inPipe.0=1 outPipe.0=3 \
--sort inPipe.0=2 outPipe.0=4 \
--derive-change inPipe.0=3 inPipe.1=4 outPipe.0=5 \
--log-progress-change inPipe.0=5 outPipe.0=6 \
--write-apidb-change host=$SLAVE_DB_HOST:$SLAVE_DB_PORT database=$SLAVE_DATABASE user=$SLAVE_DB_USER password=$SLAVE_DB_PASSWORD validateSchemaVersion=false inPipe.0=6

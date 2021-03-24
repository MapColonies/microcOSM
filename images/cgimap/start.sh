#!/usr/bin/env bash

if [ "$ENABLE_DB_CERT_AUTH" = "true" ]
then
  cp /tmp/certs/* /.postgresql
  chmod 400 /.postgresql/*.key
fi

/usr/local/bin/openstreetmap-cgimap --port=8000 --instances=30
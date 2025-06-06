#!/usr/bin/env bash
workdir="/var/www"
# Because we can not set up many env variable sin build process, we are going to process here!
# Setting up the production database
if [ "$ENABLE_DB_CERT_AUTH" = "true" ]
then
  cp /tmp/certs/* /.postgresql
  chmod 400 /.postgresql/*.key
  echo " # Production DB
production:
  adapter: postgresql
  host: ${POSTGRES_HOST}
  database: ${POSTGRES_DB}
  username: ${POSTGRES_USER}
  encoding: utf8" > $workdir/config/database.yml
else
  echo " # Production DB
production:
  adapter: postgresql
  host: ${POSTGRES_HOST}
  database: ${POSTGRES_DB}
  username: ${POSTGRES_USER}
  password: ${POSTGRES_PASSWORD}
  encoding: utf8" > $workdir/config/database.yml
fi

sed -i -e "s/export APACHE_RUN_USER=www-data/export APACHE_RUN_USER=$(whoami)/g" /etc/apache2/envvars
sed -i -e "s/export APACHE_RUN_GROUP=www-data/export APACHE_RUN_GROUP=root/g" /etc/apache2/envvars

sed -i -e 's/id_key: .*/id_application: "'$OAUTH_ID_KEY'"/g' $workdir/config/settings.yml

# Setting up the SERVER_URL and SERVER_PROTOCOL
sed -i -e "s/server_url: 'localhost'/server_url: '"$SERVER_URL"'/g" $workdir/config/settings.yml
sed -i -e "s/server_protocol: 'http'/server_protocol: '"$SERVER_PROTOCOL"'/g" $workdir/config/settings.yml

# Setting up the email
sed -i -e 's/microcosm-test@developmentseed.org/'$MAILER_USERNAME'/g' $workdir/config/settings.yml

# Print the log while compiling the assets
until $(curl -sf -o /dev/null $SERVER_URL:8080); do
    echo "Waiting to start rails ports server..."
    sleep 2
done &

# chown -R www-data:www-data /var/log/web

# chmod -R 775 www-data:www-data /var/log/web

# Precompile again, to catch the env variables
RAILS_ENV=production rake assets:precompile --trace

# db:migrate
bundle exec rails db:migrate

# Start the app
apachectl -k start -DFOREGROUND

echo "# Production DB
${RAILS_ENV}:
    adapter: postgresql
    host: ${POSTGRES_HOST}
    database: ${POSTGRES_DB}
    username: ${POSTGRES_USER}
    $([ -z "${POSTGRES_PASSWORD}" ] && echo "#")password: ${POSTGRES_PASSWORD}
    encoding: utf8" > ${WORKDIR}/config/database.yml

echo "server_url: \"${SERVER_URL}\"" >> ${WORKDIR}/config/settings.local.yml

bundle exec rake db:create
bundle exec rake db:migrate
bundle exec rails server -b 0.0.0.0
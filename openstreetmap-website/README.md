# Docker setup for openstreetmap-website

This container contains openstreetmap-website

### Configuration

- **Configure the HOST and the PROTOCOL**

  - `SERVER_URL` We need to setup the url to the server to send the email
  - `SERVER_PROTOCOL` protocol, e.g `http`

- **Configure ID editor**

  - `OAUTH_ID_KEY` the key to enable login

- **Configure ActionMailer SMTP**

  - `MAILER_ADDRESS` e.g smtp.gmail.com
  - `MAILER_DOMAIN` e.g gmail.com
  - `MAILER_USERNAME` e.g microcosm@gmail.com
  - `MAILER_PASSWORD` e.g 1234

- **Configure Postgres Database**

  - `POSTGRES_HOST` - Database host
  - `POSTGRES_DB` - Database name
  - `POSTGRES_USER` - Database user
  - `POSTGRES_PASSWORD` - Database user's password

### Building the container

### Build argument variables:
- `OSMWEB_COMMIT_SHA` - the commit SHA of openstreetmap-website to be built.

```
    docker build \
    --build-arg OSMWEB_COMMIT_SHA=d3388abe51a946ae0abc645d831a93b1b2cc6749 \
    -f ./Dockerfile -t openstreetmap-website:latest .
```

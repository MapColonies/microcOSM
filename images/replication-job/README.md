### Delta replications job container

This contain is responsible for creating the delta replication files it may be set up by minute, hour, etc. Those replications files will be uploaded to a repository in AWs of Gooble Storage, depends on what you are using.

### Configuration

In order to run this container, we should pass some environment variables

**Postgres envs**

- `POSTGRES_HOST` e.g db
- `POSTGRES_DB` e.g openstreetmap
- `POSTGRES_USER` e.g postgres
- `POSTGRES_PASSWORD` e.g 1234

The following env variables are according to which cloud provider you are going to use:

In case AWS:

- `AWS_S3_BUCKET` e.g `s3://microcosm-test`

**Replication folder**

- `REPLICATION_FOLDER`. a folder where we are going to save the data e.g `/replication/minute`

#### Building the container

```
    cd replication-job
    docker network create microcosm_default
    docker build -t microcosm-replication-job:v1 .
```

#### Running the container

```
    docker run \
    --env-file ./../.env \
    --network microcosm_default \
    -v $(pwd)/../replication-job-data:/app/data \
    -t microcosm-replication-job:v1
```

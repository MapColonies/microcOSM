# Backup and Restore the microcosm DB

This container will create a backup of the microcosm-db and compress according to the current date and then it will upload the backup file to s3 or Google store.

### Configuration

To run the container needs a bunch of ENV variables:

- `POSTGRES_HOST` - Database host
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database user's password

The following env variables are according to which cloud provider you are going to use:

- `CLOUDPROVIDER`, eg. `aws`

In case AWS:

- `AWS_S3_BUCKET` e.g `s3://microcosm-test`

_Database action_

- `DB_ACTION` e.g `backup` or `restore`

Change the `DB_ACTION` variable to restore or backup the database. `DB_ACTION` = `restore` or `backup`

### Building the container

```
  cd db-backup-restore/
  docker network create microcosm_default
  docker build -t microcosm-db-backup-restore:v1 .
```

### Running the container

```
docker run \
--env-file ./../.env \
--network microcosm_default \
-it microcosm-db-backup-restore:v1
```

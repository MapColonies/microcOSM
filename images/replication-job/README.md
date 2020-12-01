### Minute replications job container

This contain is responsible for creating the delta replication files it may be set up by minute.
The container uses osmosis.

### Configuration

In order to run this container, we should pass some environment variables

**Postgres envs**

- `POSTGRES_HOST` e.g db
- `POSTGRES_DB` e.g openstreetmap
- `POSTGRES_USER` e.g postgres
- `POSTGRES_PASSWORD` e.g 1234
- `REPLICATION_DIRECTORY`. a folder where we are going to save the minute replications e.g `/mnt/replication`

# osm2pgsql

This container is responsible for importing the replication osmChange files from microcosm (created by the `replication-job ` container) or an external source into the `tiler-db` in the main tiler pipeline.

With every import\append configuration files that indicate the data scheme needs to be specified. Note that once the database is populated with the first import the same configurtion needs to be appended. [read more](#Database-columns-structure)

Appending changes to exising source of data will result in list of expired tiles which will be saved in the replication files fashion (`/mnt/expired/x/y/z-expire.list`). Where x,y,z are derived from the replication sequence number of that same replication. `mod-tile` will re-render the expired tiles based on the new data entered in `tiler-db`.

Appended changes are being tracked in the `state.txt` file placed in `/mnt/expired/`.
The `sequenceNumber` key states the last replication sequence number created by `replication-job` container and `lastAppend` key states the last replication appended by `osm2pgsql`.

### Configuration

**Env Variables to connect to the tiles db**

- `POSTGRES_HOST` e.g `tiler-db`
- `POSTGRES_DB` e.g `tiler-osm`
- `POSTGRES_PORT` e.g `5432`
- `POSTGRES_USER` e.g `postgres`
- `POSTGRES_PASSWORD` e.g `1234`
- `REPLICATION_URL` e.g `http://static-server/replication/minute`
- `OSM2PGSQL_UPDATE_INTERVAL` e.g `60` (60 seconds)
- `EXPIRED_DIR` e.g `/mnt/expired`
- 

  **Env Variables to update data**

- `OSM2PGSQL_UPDATE_INTERVAL` the interval in **seconds** for `osm2pgsql` to append replication files into the `tiler-db`.
- `REPLICATION_URL` the url to retrieve the replication files from.
- `EXPIRED_DIR` the folder to save the lists of expired tiles to.

#### **Database columns structure**

The OpenStreetMap-Carto database scheme is being used

- `osm2pgsql` supports Lua scripts to rewrite tags before they enter the database.
  This allows to unify disparate tagging and perform complex queries, potentially more efficiently than writing them as rules in Mapnik.
  [more info](https://github.com/openstreetmap/osm2pgsql/blob/master/docs/lua.md)
- importing\appending data requires a `.style` file that has 4 columns that define how OSM objects end up in tables in the database and what columns are created.
  [more info](https://github.com/openstreetmap/osm2pgsql/blob/master/default.style)

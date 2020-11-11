# Tiler imposm

This container is responsible to import the replication PBF files from microcosm or OSM planet dump into the `vector-tiles-db`

If we are running the container for the first time the container will import the [OSM Land](http://data.openstreetmapdata.com/land-polygons-split-3857.zip) and [Natural Earth dataset](http://nacis.org/initiatives/natural-earth) and [osm-land] files into the data bases. [Check more here](https://github.com/go-spatial/tegola-osm#import-the-osm-land-and-natural-earth-dataset-requires-gdal-natural-earth-can-be-skipped-if-youre-only-interested-in-osm).

### Configuration

Required environment variables:

**Env variables to connect to the vector-tiles-db**

- `POSTGRES_HOST` e.g `tiler-db`
- `POSTGRES_DB` e.g `tiler-osm`
- `POSTGRES_PORT` e.g `5432`
- `POSTGRES_USER` e.g `postgres`
- `POSTGRES_PASSWORD` e.g `1234`

  **Env variables to import the files**

- `CONFIG_REPLICATION_INTERVAL` the time between replications with the time unit (1m for a minute, 1h for an hour)
- `IMPOSM_REPLICATION_URL` the url to the replication files
- `CONFIG_EXPIRED_TILES_ZOOM` the zoom to expire tiles on update
- `CONFIG_EXPIRED_TILES_DIR` the directory inside the container to save the expired tiles lists

#### Building the container

```
    cd imposm/
    docker network create microcosm_default
    docker build -t microcosm-imposm:v1 .
```

#### Running the container

```
    docker run \
    --env-file ./../.env-tiler \
    --network microcosm_default \
    -t microcosm-imposm:v1
```

# tegola

This container is for rendering the vector tiles base on [Tegola](https://github.com/go-spatial/tegola), the container connects to the database `tiler-db` and serves the tiles through the port `9090`.

### Configuration

Required environment variables:

**Env variables to connect to the db-tiler**

- `OSM_POSTGRES_HOST` db with osm data for rendering host
- `OSM_POSTGRES_PORT` db with osm data for rendering port
- `OSM_POSTGRES_DB` db with osm data for rendering db
- `OSM_POSTGRES_USER` db with osm data for rendering user
- `OSM_POSTGRES_PASSWORD` db with osm data for rendering password

- `EARTH_TILES_POSTGRES_HOST` db with earth tiles for rendering host
- `EARTH_TILES_POSTGRES_PORT` db with earth tiles for rendering port
- `EARTH_TILES_POSTGRES_DB` db with osm data for rendering db
- `EARTH_TILES_POSTGRES_USER` db with osm data for rendering user
- `EARTH_TILES_POSTGRES_PASSWORD` db with osm data for rendering password

\*\*

**Env variables to update the tiles**

- `EXPIRE_TILES_DIR` the folder inside the container where the expire dir is mounted
- `TILER_CACHE_UPDATE_INTERVAL` the time to wait between updating tiles in seconds

**Env variables to serve the tiles**

- `TILER_SERVER_PORT` e.g `9090`
- `URI_PREFIX` the start string for the uri e.g `mvt`

**Env variables for caching the tiles**

TILER*CACHE*\* , by default microcosm-tiler is using aws-s3 for caching the tiles, if you want to change it, take a look in: https://github.com/go-spatial/tegola/tree/master/cache

- `TILER_SERVER_PORT` e.g `9090`
- `TILER_CACHE_TYPE` e.g `s3` or `file`
- `TILER_CACHE_BUCKET` e.g `s3://microcosm-tiler`
- `TILER_CACHE_BASEPATH` e.g `local`
- `TILER_CACHE_REGION` e.g `us-east-1`
- `TILER_CACHE_AWS_ACCESS_KEY_ID` e.g `xyz`
- `TILER_CACHE_AWS_SECRET_ACCESS_KEY` e.g `xyz`
- `TILER_CACHE_MAX_ZOOM` e.g `19` - the max zoom value for tile expiry
- `TILER_CACHE_MIN_ZOOM` e.g `14` - the min zoom value for tile expiry

#### Building the container

```
    cd tiler-server/
    docker network create microcosm_default
    docker build -t microcosm-tiler-server:v1 .
```

#### Running the container

```
  docker run \
  --env-file ./../.env-tiler \
  --network microcosm_default \
  -v $(pwd)/../tiler-server-data:/mnt/data \
  -p "9090:9090" \
  -t microcosm-tiler-server:v1
```

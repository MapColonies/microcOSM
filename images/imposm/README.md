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

- `IMPOSM_IMPORT_PBF_URL` eg `http://download.geofabrik.de/south-america/peru-latest.osm.pbf`
- `TILER_IMPORT_LIMIT` geojson url
- `IMPOSM_MAPPING_FILE` imposm yaml\json mapping file. the `vector-tiles-db` will be mapped according to

If you are setting up the variable TILER_IMPORT_PROM=`microcosm` you should fill following env variables according to which cloud provider you are going to use

- `CLOUDPROVIDER`, eg. `aws`

In case AWS:

- `AWS_S3_BUCKET` e.g `s3://microcosm-test`

Note: In case you use the `TILER_IMPORT_PROM`=`microcosm` you need to make public the minute replication files to update the DB with the recent changes.

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

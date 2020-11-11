# OSM2PGSQL

## Introduction
`osm2pgsql` is a command-line based program that converts OpenStreetMap data to postGIS-enabled PostgreSQL databases.

## Requirements
1. `openfirmware/postgres-osm:9.3.6` from Dockerhub, [link](https://hub.docker.com/r/openfirmware/postgres-osm). This image uses `PostgresSQL` version `9.3.6` with `PostGIS` and `HStore` extensions installed.

2. `openfirmware/osm2pgsql:0.87.2` from Dockerhub, [link](https://hub.docker.com/r/openfirmware/osm2pgsql). This image uses `osm2pgsql` cli version `0.87.2`.

## Steps
1. First you need to acquire an osm file, for example run the following command: `wget -O ~/osm/petah-tikva.osm "https://api.openstreetmap.org/api/0.6/map?bbox=34.8596465588,32.0697517118,34.8702895641,32.0821155073"` the `bbox` in the query param is a bounding box of a neighborhood in `Petah-Tikva` city. if you run the command it will save the file in `~/osm/petah-tikva.osm` make sure you have the proper directories.

2. Pull the images `openfirmware/postgres-osm:9.3.6` , `openfirmware/osm2pgsql:0.87.2`

3. Run the `openfirmware/postgres-osm:9.3.6` image with the following command `docker run -d --name postgres-osm -p 5432:5432 openfirmware/postgres-osm`.

4. Run the  `openfirmware/osm2pgsql:0.87.2` image with the following command ` docker run -it --rm --link postgres-osm:pg -v ~/osm:/osm openfirmware/osm2pgsql -c 'osm2pgsql --create --slim --cache 2000 --database gis --username osm --host pg --port 5432 /osm/petah-tikva.osm'` it will load the osm file into the database

5. [OPTIONAL] you can run a `pg-admin` for `localhost:5432` with postgres postgres as username and password.

# Important notes
Taken from the `postgres-osm` Dockerfile 

```sh
ENV OSM_USER osm
ENV OSM_DB gis
```

by default osm and gis is the username db name.

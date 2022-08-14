# CGI map


This container contains cgimap - an high performence partial implementation of the osm api

### Configuration

Required environment variables:

**Env variables to connect to the vector-tiles-db**

- `CGIMAP_HOST` e.g `osm-db`
- `CGIMAP_DBNAME` e.g `osm`
- `CGIMAP_USER` e.g `postgres`
- `CGIMAP_PASSWORD` e.g `1234`

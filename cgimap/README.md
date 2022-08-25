# CGI map

This container contains cgimap - an high performence partial implementation of the osm api

## Building

### Build argument variables
- `CGIMAP_TAG` - the version tag of cgimap, defaults to v0.8.3

### Building the container

```
    docker build \
    --build-arg CGIMAP_TAG=v0.8.8 \
    -f ./Dockerfile -t cgimap:latest .
```

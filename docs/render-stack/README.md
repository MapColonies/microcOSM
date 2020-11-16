# Render Stack

microcosm stack comes without some fundamental components for a full OSM environment. The microcosm-renderer stack contains the missing pieces and has the following containers:

- `mod-tile` - contains the components responsible for handling the tile rendering, expiring and serving.
- `osm2pgsql` - used for importing and updating data into the `tiler-db` instead of `imposm` container.
- `tiler-db` - same as the microcosm original `tiler-db` but populated with `osm2pgsql` using the `openstreetmap-carto` style.

The map tiles rendered on the `openstreetmap-website` can now be fetched from the local environment instead of the global osm website.

Local edits on the osm data will result in tiles to be expired and re-rendered, the effect will take place on the `openstreetmap-website` every minute (by default)

After rendering a tile, it gets cached on disk for fast serving. As OSM data is constantly updated, improved and changed, a mechanism is needed to correctly expire the cache to ensure updated tiles get re-rendered.

- OsmChanges of the local microcosm are being created by `replication-job` container and saved on `REPLICATION_DIR`
- `osm2pgsql` reads the osmChanges from `REPLICATION_DIR` and appends the data onto the `tiler-db`, every append is configured with style and rules that indicate the data scheme and affects how `mod-tile`'s renderd will render the tiles.
- Each append outputs an expired tiles list - the tiles whose data has been updated in the append, the lists is being saved in `EXPIRED_DIR`.
- A list of all the expired tiles since the last render will be composed and saved in `EXPIRED_DIR/currentlyExpired.list`, for performance duplicates will be removed.
- `mod-tile`'s `mod_tile` will expire the cached tiles specified in the `currentlyExpired.list` and will re-render and cache them on the disk when they will be requested from `mod_tile`.
- The tiles will be served by `mod-tile`'s `mod_tile` for clients on the `openstreetmap-website`

The state of the rendered tiles is being tracked by `state.txt` and `renderedState.txt` files located in `EXPIRED_DIR`
- `state.txt`
    - `sequenceNumber` - each osm2pgsql append function is fetching the last replication `sequenceNumber` from `replication-job` container and saves it in `state.txt`
    - `lastExpired` - the last replication sequenceNumber expired by `osm2pgsql` append.
- `renderedState.txt`
    - `lastRendered` - the last rendered replication `sequenceNumber` marked expired by `mod-tile`.

![Alt text](./microcosm-renderer-diagram.png?raw=true 'Diagram')

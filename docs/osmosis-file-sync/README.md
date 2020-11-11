# Osmosis file sync

## File sync into populated DB

In Order to populate a file into an already popluated DB we need create a change stream comparing the file with the DB. 
Run the following osmosis command:
``` bash
osmosis \ 
    --rb file="/osm-data/belize-latest.osm.pbf" \
    --rd authFile="/osm-data/dbfile" allowIncorrectSchemaVersion="yes" \
    --bounding-polygon file="/osm-data/belize.poly" \ 
     --dc \
     --write-apidb-change authFile="/osm-data/dbfile"   validateSchemaVersion="no"  
```

* --rb 
  * reads a pbf file from the provided path in the ```file``` param . creates an entity stream.
* --rd 
  * reads a DB from provide DB configuration in the ```authFile``` param.
  * More on ```authfile``` format [here](https://wiki.openstreetmap.org/wiki/Osmosis/Detailed_Usage_0.48#Database_Login_Credentials)
  *  --bounding-polygon 
     * when Creating a change stream between a file and a populated DB it will alson include all the existing DB data the don't exists in the file as changes which will result in large change stream. In order to include only the changes in the file we need to filter the relevant data from the DB by polygon.
     In the example above the pbf was downloaded from [geofabrik](https://download.geofabrik.de/central-america/belize.html) which also provide the ```.poly``` file from which the pbf was created.
     also possible to filter by bounding box. more on polygons and box [here](https://wiki.openstreetmap.org/wiki/Osmosis/Detailed_Usage_0.48#Area_Filtering_Tasks) 
* --dc 
  * Create the change stream from the the entity stream.
* --write-apidb-change
  * writes the change stream into the DB provided in the ```authfile```

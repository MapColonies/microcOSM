#!/bin/bash
set -e
mkdir -p /tmp
stateFile="state.txt"
PBFFile="first-osm-import.pbf"
limitFile="limitFile.geojson"
# diffStateBefore="1h"
flag=true

# directories to keep the imposm's cache for updating the db
cachedir="/mnt/data/cachedir"
mkdir -p $cachedir
diffdir="/mnt/data/diff"
mkdir -p $diffdir
expiretilesdir="/mnt/expiretiles"
mkdir -p $expiretilesdir

# Create config file to set variable for imposm
echo "{" > config.json
echo "\"cachedir\": \"$cachedir\","  >> config.json
echo "\"diffdir\": \"$diffdir\","  >> config.json
echo "\"expiretiles_dir\": \"$expiretilesdir\","  >> config.json
echo "\"expiretiles_zoom\": 14,"  >> config.json
echo "\"connection\": \"postgis://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST/$POSTGRES_DB\"," >> config.json
echo "\"mapping\": \"$IMPOSM_MAPPING_FILE\","  >> config.json
echo "\"replication_url\": \"$IMPOSM_REPLICATION_URL\","  >> config.json
echo "\"replication_interval\": \"$IMPOSM_REPLICATION_INTERVAL\""  >> config.json
# echo "\"diff_state_before\": \"$diffStateBefore\""  >> config.json
echo "}" >> config.json

# function getData () {
#     # Import from pubic url, ussualy it come from osm
#     if [ $IMPOSM_IMPORT_FROM == "osm" ]; then 
#         wget $IMPOSM_IMPORT_PBF_URL -O $PBFFile
#     fi

#     if [ $IMPOSM_IMPORT_FROM == "osmseed" ]; then 
#         if [ $CLOUDPROVIDER == "aws" ]; then 
#             # Get the state.txt file from S3
#             aws s3 cp $AWS_S3_BUCKET/planet/full-history/$stateFile .
#             PBFCloudPath=$(tail -n +1 $stateFile)
#             aws s3 cp $PBFCloudPath $PBFFile
#         fi
#     fi
# }


function initializeDatabase () {
    echo "Execute the missing functions"
    psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST/$POSTGRES_DB" -a -f postgis_helpers.sql
    psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST/$POSTGRES_DB" -a -f postgis_index.sql
    echo "Import Natural Earth"
    ./scripts/natural_earth.sh
    echo "Import OSM Land"
    ./scripts/osm_land.sh
}

function importData () {
    echo "Import PBF file"

    imposm import \
    -config config.json \
    -read $PBFFile \
    -write \
    -diff \
    -diffdir $diffdir \
    -cachedir $cachedir

    imposm import \
    -config config.json \
    -deployproduction

    # Update the DB
    updateData
}

function updateData () {
    # if [ -z "$TILER_IMPORT_LIMIT" ]; then
        imposm run -config config.json & 
        while true
        do 
            echo "Updating...$(date +%F_%H-%M-%S)"
            sleep 1m
        done
    # else
    #     imposm run -config config.json -limitto /mnt/data/$limitFile &
    #     while true
    #     do 
    #         echo "Updating...$(date +%F_%H-%M-%S)"
    #         sleep 1m
    #     done
    # fi
}

echo "Connecting... to postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST/$POSTGRES_DB"

while "$flag" = true; do
    echo "trying to connect to $POSTGRES_HOST..."
    pg_isready -h $POSTGRES_HOST -p 5432 >/dev/null 2>&2 || continue
        # Change flag to false to stop ping the DB
        flag=false
        hasData=$(psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST/$POSTGRES_DB" \
        -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'" | sed -n 3p | sed 's/ //g')

        echo $hasData

        # After import there are more than 70 tables
        if [ $hasData  \> 70 ]; then
            echo "Start importing data to existing database"
            updateData
        else
            echo "Start importing the data"
            initializeDatabase
            # if [ -n "$IMPOSM_IMPORT_PBF_URL" ]; then
            #     echo "Import PBF data to DB"
            #     getData
            # else

            until $(curl --output /dev/null --silent --head --fail ${IMPOSM_REPLICATION_URL}000/000/000.state.txt); do
              printf 'waiting for state file...'
              sleep 5
            done

            curl --output /mnt/data/diff/last.state.txt ${IMPOSM_REPLICATION_URL}000/000/000.state.txt
            dateString=$(sed '4q;d' /mnt/data/diff/last.state.txt | sed 's/\\//g' | cut -d "=" -f2-)

            touch -d $dateString $PBFFile 
            # fi
            importData
        fi
done
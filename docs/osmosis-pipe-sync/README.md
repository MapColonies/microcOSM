# Osmosis pipe sync

## Introduction
`Osmosis` container for 1 way sync between two OSM databases.

## Configuration
1. Create `.env` file to hold all the environment variables: 
    ```
    cp .env.example .env
    ```
2. Edit `.env` file with your database connection options

## Sync script
`start.sh` based on `Osmosis/Detailed Usage 0.48`:

https://wiki.openstreetmap.org/wiki/Osmosis/Detailed_Usage_0.48

# Image Usage

1. Run `docker build -t mapcolonies/osmosis:0.48.2 -f ../../images/osmosis/Dockerfile .`
2. Run `docker build -t osmosis-one-way-sync .`
2. Run `docker run --rm --env-file=./.env osmosis-one-way-sync`

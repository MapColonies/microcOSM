#!/usr/bin/env bash
set -e

echo "Import Natural Earth"
./scripts/natural_earth.sh
echo "Import OSM Land"
./scripts/osm_land.sh
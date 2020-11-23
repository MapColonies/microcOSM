#!/bin/bash
set -e
set sha=$(git rev-parse HEAD)

for d in */ ; do
  if [ -f "${d}Dockerfile" ]; then
    echo -e "running docker build -t microcosm-${d%/}:latest ${d}${NC}"
    echo docker build -q -t $sha -t http://645470188746.dkr.ecr.eu-west-1.amazonaws.com/$d:latest
    echo docker push http://645470188746.dkr.ecr.eu-west-1.amazonaws.com/$d
  fi
done

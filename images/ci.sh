#!/bin/bash
echo $PWD
set -e
SHA=`git rev-parse HEAD`
TAG=`git describe --abbrev=0 --tags`
ECR=645470188746.dkr.ecr.eu-west-1.amazonaws.com
PROJECT=microcosm
echo $TAG
for d in */ ; do
  if [ -f "${d}Dockerfile" ]; then
    filename=$(basename -- "$d")
    foldername=${filename%.*}
    echo $filename
    echo -e "running docker build -q -t ${SHA} -t ${ECR}/${PROJECT}-${foldername}:${TAG}"
    cd $foldername
    docker build -q -t $SHA -t $ECR/${PROJECT}-$foldername:$TAG .
    docker push $ECR/${PROJECT}-$foldername:$TAG
    cd ..
  fi
done

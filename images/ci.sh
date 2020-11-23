
#!/bin/bash
echo $PWD
set -e
SHA=`git rev-parse HEAD`
#TAG=`git tag`
TAG=`git describe --tags --abbrev=0`
ECR=http://645470188746.dkr.ecr.eu-west-1.amazonaws.com
echo $TAG
for d in */ ; do
  if [ -f "${d}Dockerfile" ]; then
    filename=$(basename -- "$d")
    foldername=${filename%.*}
    echo $filename
    echo -e "running docker build -t microcosm-${foldername}:$TAG ${d}${NC}"
    echo docker build -q -t $SHA -t $ECR/$foldername:$TAG
    echo docker push $ECR/$foldername:$TAG
  fi
done

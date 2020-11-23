
#!/bin/bash
set -e
SHA=$(git rev-parse HEAD)
TAG=$(git describe)
ECR=http://645470188746.dkr.ecr.eu-west-1.amazonaws.com
echo $SHA
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


#!/bin/bash
set -e
SHA=$(git rev-parse HEAD)
echo $SHA
for d in */ ; do
  if [ -f "${d}Dockerfile" ]; then
    filename=$(basename -- "$d")
    foldername=${filename%.*}
    echo $filename
    echo -e "running docker build -t microcosm-${foldername}:latest ${d}${NC}"
    echo docker build -q -t $SHA -t http://645470188746.dkr.ecr.eu-west-1.amazonaws.com/$foldername:latest
    echo docker push http://645470188746.dkr.ecr.eu-west-1.amazonaws.com/$foldername:latest
  fi
done

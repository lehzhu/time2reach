#!/bin/bash

set -e

echo "Logging in..."
docker login ghcr.io -u USERNAME -p $1

docker pull ghcr.io/econaxis/test:latest

echo "Killing existing containers if exist"
docker kill main &> /dev/null  || :
docker rm main &> /dev/null  || :
sleep 1

echo "Running new container"
docker run --rm --name main -d -p 443:3030 -v $HOME/vancouver-cache:/tmp/vancouver-cache:ro -e RUST_LOG=info,timetoreach=debug,h2=info,hyper=info,warp=info,rustls=info ghcr.io/econaxis/test:latest

echo Run docker logs main -f
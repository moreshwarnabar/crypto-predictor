#!/bin/bash

# builds a docker image for a service and pushes it to a registry

service=$1
env=$2

# check if service is provided
if [ -z "$service" ]; then
    echo "Usage: $0 <service> <env>"
    exit 1
fi

# check if env is provided
if [ -z "$env" ]; then
    echo "Usage: $0 <service> <env>"
    exit 1
fi

# check if env is valid
if [ "$env" != "dev" ] && [ "$env" != "prod" ]; then
    echo "Usage: $0 <service> <env>"
    exit 1
fi

# build the image for dev environment
if [ "$env" == "dev" ]; then
    echo "Building image for dev environment"
    docker build -t ${service}:dev -f docker/${service}.Dockerfile .
    kind load docker-image ${service}:dev --name crypto-cluster
else
    echo "Building image for prod environment"
    BUILD_DATE=$(date +%s)
    docker buildx build --push \
        --platform linux/amd64 \
        -t ghcr.io/moreshwarnabar/crypto-${service}:0.1.1-beta.${BUILD_DATE} \
        -f docker/${service}.Dockerfile .
fi

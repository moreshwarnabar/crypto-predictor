#! /bin/bash

# deploys a service to a given environment

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

cd deployments/${env}
eval $(direnv export bash)
echo "KUBECONFIG: ${KUBECONFIG}"

kubectl delete -f ${service}/${service}.yaml --ignore-not-found=true
kubectl apply -f ${service}/${service}.yaml

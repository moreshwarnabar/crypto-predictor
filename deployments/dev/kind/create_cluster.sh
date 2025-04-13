#!/bin/bash
# Steps:

# 1. Delete the cluster (if it exists, otherwise it will fail)
echo "Deleting the cluster..."
kind delete cluster --name crypto-cluster

# 2. Delete the docker network (if it exists, otherwise it will fail)
echo "Deleting the docker network..."
docker network rm crypto-network

# 3. Create the docker network
echo "Creating the docker network..."
docker network create --subnet 172.100.0.0/16 crypto-network

# 4. Create the cluster
echo "Creating the cluster..."
KIND_EXPERIMENTAL_DOCKER_NETWORK=crypto-network kind create cluster --config ./kind-with-portmapping.yaml

# 5. Install Kafka
echo "Installing Kafka..."
chmod +x ./install_kafka.sh
./install_kafka.sh

# 6. Install Kafka UI
echo "Installing Kafka UI..."
chmod +x ./install_kafka_ui.sh
./install_kafka_ui.sh
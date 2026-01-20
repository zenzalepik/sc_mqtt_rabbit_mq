#!/bin/bash

# Stop-RabbitMQ-Cluster.sh
# Stops the 3-node RabbitMQ Cluster on Linux/RasPi

echo "Stopping RabbitMQ Cluster..."

NODE1_NAME="rabbit1@localhost"
NODE2_NAME="rabbit2@localhost"
NODE3_NAME="rabbit3@localhost"

stop_node() {
    NODE=$1
    echo "Stopping $NODE..."
    export RABBITMQ_NODENAME=$NODE
    rabbitmqctl stop
}

stop_node $NODE3_NAME
stop_node $NODE2_NAME
stop_node $NODE1_NAME

echo "Cluster Stopped."

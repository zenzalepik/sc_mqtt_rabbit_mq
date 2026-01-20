#!/bin/bash

# Start-RabbitMQ-Cluster.sh
# Starts a 3-node RabbitMQ Cluster for High Availability Testing on Linux/RasPi

echo "Starting RabbitMQ Cluster (3 Nodes)..."

# --- CONFIGURATION ---
NODE1_NAME="rabbit1@localhost"
NODE2_NAME="rabbit2@localhost"
NODE3_NAME="rabbit3@localhost"

# Data Directories
BASE_DIR="$HOME/rabbitmq_cluster_data"
mkdir -p "$BASE_DIR/node1"
mkdir -p "$BASE_DIR/node2"
mkdir -p "$BASE_DIR/node3"

echo "Data Directories created at $BASE_DIR"

# Check for rabbitmq-server
if ! command -v rabbitmq-server &> /dev/null; then
    echo "ERROR: rabbitmq-server could not be found."
    echo "Please install RabbitMQ (e.g., sudo apt-get install rabbitmq-server)"
    exit 1
fi

# --- START NODE 1 (MASTER) ---
echo "Starting Node 1..."
export RABBITMQ_NODENAME=$NODE1_NAME
export RABBITMQ_NODE_PORT=5672
export RABBITMQ_DIST_PORT=25672
export RABBITMQ_BASE="$BASE_DIR/node1"
export RABBITMQ_SERVER_START_ARGS="-rabbitmq_management listener [{port,15672}] -rabbitmq_mqtt tcp_listeners [1883]"
export RABBITMQ_PID_FILE="$BASE_DIR/node1.pid"

rabbitmq-server -detached

echo "Waiting 10s for Node 1 to initialize..."
sleep 10

# --- START NODE 2 ---
echo "Starting Node 2..."
export RABBITMQ_NODENAME=$NODE2_NAME
export RABBITMQ_NODE_PORT=5673
export RABBITMQ_DIST_PORT=25673
export RABBITMQ_BASE="$BASE_DIR/node2"
export RABBITMQ_SERVER_START_ARGS="-rabbitmq_management listener [{port,15673}] -rabbitmq_mqtt tcp_listeners [1884]"
export RABBITMQ_PID_FILE="$BASE_DIR/node2.pid"

rabbitmq-server -detached

# --- START NODE 3 ---
echo "Starting Node 3..."
export RABBITMQ_NODENAME=$NODE3_NAME
export RABBITMQ_NODE_PORT=5674
export RABBITMQ_DIST_PORT=25674
export RABBITMQ_BASE="$BASE_DIR/node3"
export RABBITMQ_SERVER_START_ARGS="-rabbitmq_management listener [{port,15674}] -rabbitmq_mqtt tcp_listeners [1885]"
export RABBITMQ_PID_FILE="$BASE_DIR/node3.pid"

rabbitmq-server -detached

echo "Waiting 15s for nodes to fully start..."
sleep 15

# --- CLUSTERING ---
echo "Joining Nodes to Cluster..."

# Join Node 2 to Node 1
export RABBITMQ_NODENAME=$NODE2_NAME
rabbitmqctl stop_app
rabbitmqctl join_cluster $NODE1_NAME
rabbitmqctl start_app

# Join Node 3 to Node 1
export RABBITMQ_NODENAME=$NODE3_NAME
rabbitmqctl stop_app
rabbitmqctl join_cluster $NODE1_NAME
rabbitmqctl start_app

echo "Cluster Status:"
export RABBITMQ_NODENAME=$NODE1_NAME
rabbitmqctl cluster_status

echo "Cluster Started Successfully!"

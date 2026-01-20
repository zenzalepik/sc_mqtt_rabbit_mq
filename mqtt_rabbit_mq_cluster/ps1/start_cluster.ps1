# Start-RabbitMQ-Cluster.ps1
# Starts a 3-node RabbitMQ Cluster for High Availability Testing on Localhost
# Requires RabbitMQ and Erlang to be installed and in PATH

Write-Host "Starting RabbitMQ Cluster (3 Nodes)..." -ForegroundColor Cyan

# Configuration
$Node1_Name = "rabbit1@localhost"
$Node2_Name = "rabbit2@localhost"
$Node3_Name = "rabbit3@localhost"

# Base Data Directories (to avoid conflicts)
$AppData = $env:APPDATA
$BaseDir1 = "$AppData\RabbitMQ_Node1"
$BaseDir2 = "$AppData\RabbitMQ_Node2"
$BaseDir3 = "$AppData\RabbitMQ_Node3"

# Ensure directories exist
New-Item -ItemType Directory -Force -Path $BaseDir1 | Out-Null
New-Item -ItemType Directory -Force -Path $BaseDir2 | Out-Null
New-Item -ItemType Directory -Force -Path $BaseDir3 | Out-Null

Write-Host "Data Directories created at $AppData\RabbitMQ_Node*" -ForegroundColor Gray

# Function to start a node asynchronously
function Start-RabbitMQNode {
    param(
        [string]$NodeName,
        [string]$NodePort,
        [string]$DistPort,
        [string]$MgmtPort,
        [string]$MqttPort,
        [string]$BaseDir
    )

    $Env:RABBITMQ_NODENAME = $NodeName
    $Env:RABBITMQ_NODE_PORT = $NodePort
    $Env:RABBITMQ_DIST_PORT = $DistPort
    $Env:RABBITMQ_BASE = $BaseDir
    # Arguments to enable plugins on specific ports
    $Env:RABBITMQ_SERVER_START_ARGS = "-rabbitmq_management listener [{port,$MgmtPort}] -rabbitmq_mqtt tcp_listeners [$MqttPort]"

    Write-Host "Starting $NodeName (AMQP:$NodePort, MQTT:$MqttPort, Mgmt:$MgmtPort)..." -ForegroundColor Green
    
    # Start in new window to keep running
    Start-Process -FilePath "rabbitmq-server.bat" -NoNewWindow
}

# --- START NODE 1 (MASTER) ---
# Reset Env for Node 1
$Env:RABBITMQ_NODENAME = $Node1_Name
$Env:RABBITMQ_NODE_PORT = "5672"
$Env:RABBITMQ_DIST_PORT = "25672"
$Env:RABBITMQ_BASE = $BaseDir1
$Env:RABBITMQ_SERVER_START_ARGS = "-rabbitmq_management listener [{port,15672}] -rabbitmq_mqtt tcp_listeners [1883]"

Write-Host "Starting Node 1..." -ForegroundColor Green
Start-Process "cmd.exe" -ArgumentList "/c rabbitmq-server.bat" -WindowStyle Minimized

Write-Host "Waiting 10s for Node 1 to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# --- START NODE 2 ---
$Env:RABBITMQ_NODENAME = $Node2_Name
$Env:RABBITMQ_NODE_PORT = "5673"
$Env:RABBITMQ_DIST_PORT = "25673"
$Env:RABBITMQ_BASE = $BaseDir2
$Env:RABBITMQ_SERVER_START_ARGS = "-rabbitmq_management listener [{port,15673}] -rabbitmq_mqtt tcp_listeners [1884]"

Write-Host "Starting Node 2..." -ForegroundColor Green
Start-Process "cmd.exe" -ArgumentList "/c rabbitmq-server.bat" -WindowStyle Minimized

# --- START NODE 3 ---
$Env:RABBITMQ_NODENAME = $Node3_Name
$Env:RABBITMQ_NODE_PORT = "5674"
$Env:RABBITMQ_DIST_PORT = "25674"
$Env:RABBITMQ_BASE = $BaseDir3
$Env:RABBITMQ_SERVER_START_ARGS = "-rabbitmq_management listener [{port,15674}] -rabbitmq_mqtt tcp_listeners [1885]"

Write-Host "Starting Node 3..." -ForegroundColor Green
Start-Process "cmd.exe" -ArgumentList "/c rabbitmq-server.bat" -WindowStyle Minimized

Write-Host "Waiting 15s for nodes to fully start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# --- CLUSTERING ---
Write-Host "Joining Nodes to Cluster..." -ForegroundColor Cyan

# Helper to run rabbitmqctl with specific node env
function Run-Ctl {
    param($NodeName, $Cmd, $Arg)
    $Env:RABBITMQ_NODENAME = $NodeName
    rabbitmqctl.bat $Cmd $Arg
}

# Join Node 2 to Node 1
Write-Host "Joining Node 2 to Node 1..."
$Env:RABBITMQ_NODENAME = $Node2_Name
rabbitmqctl.bat stop_app
rabbitmqctl.bat join_cluster $Node1_Name
rabbitmqctl.bat start_app

# Join Node 3 to Node 1
Write-Host "Joining Node 3 to Node 1..."
$Env:RABBITMQ_NODENAME = $Node3_Name
rabbitmqctl.bat stop_app
rabbitmqctl.bat join_cluster $Node1_Name
rabbitmqctl.bat start_app

Write-Host "Cluster Setup Complete!" -ForegroundColor Green
Write-Host "Monitor URLs:"
Write-Host "Node 1: http://localhost:15672"
Write-Host "Node 2: http://localhost:15673"
Write-Host "Node 3: http://localhost:15674"
Write-Host "Default Login: guest / guest"

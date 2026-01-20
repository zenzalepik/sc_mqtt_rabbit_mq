# Stop-RabbitMQ-Cluster.ps1

Write-Host "Stopping RabbitMQ Cluster..." -ForegroundColor Yellow

$Node1_Name = "rabbit1@localhost"
$Node2_Name = "rabbit2@localhost"
$Node3_Name = "rabbit3@localhost"

function Stop-Node {
    param($NodeName)
    Write-Host "Stopping $NodeName..."
    $Env:RABBITMQ_NODENAME = $NodeName
    try {
        rabbitmqctl.bat stop
    } catch {
        Write-Host "Failed to stop $NodeName (might be already stopped)" -ForegroundColor Red
    }
}

Stop-Node $Node3_Name
Stop-Node $Node2_Name
Stop-Node $Node1_Name

# Kill any lingering erl.exe processes started by us (Use with caution)
# Get-Process erl -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Cluster Stopped." -ForegroundColor Green

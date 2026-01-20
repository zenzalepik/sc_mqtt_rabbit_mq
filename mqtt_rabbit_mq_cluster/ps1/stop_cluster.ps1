# Stop-RabbitMQ-Cluster.ps1
# Supports Portable Mode

Write-Host "Stopping RabbitMQ Cluster..." -ForegroundColor Yellow

# --- PORTABLE MODE DETECTION ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$RepoRoot = Split-Path -Parent $ProjectRoot
$ToolsDir = Join-Path $RepoRoot "tools"

$ErlangHome = Join-Path $ToolsDir "erlang"
$RabbitHome = Join-Path $ToolsDir "rabbitmq"

$RabbitCtlCmd = "rabbitmqctl.bat"

if ((Test-Path "$ErlangHome\bin\erl.exe") -and (Test-Path "$RabbitHome\sbin\rabbitmq-server.bat")) {
    $env:ERLANG_HOME = $ErlangHome
    $env:RABBITMQ_HOME = $RabbitHome
    $env:PATH = "$ErlangHome\bin;$RabbitHome\sbin;$env:PATH"
    $RabbitCtlCmd = "$RabbitHome\sbin\rabbitmqctl.bat"
}

$Node1_Name = "rabbit1@localhost"
$Node2_Name = "rabbit2@localhost"
$Node3_Name = "rabbit3@localhost"

function Stop-Node {
    param($NodeName)
    Write-Host "Stopping $NodeName..."
    $Env:RABBITMQ_NODENAME = $NodeName
    try {
        & $RabbitCtlCmd stop
    } catch {
        Write-Host "Failed to stop $NodeName (might be already stopped)" -ForegroundColor Red
    }
}

Stop-Node $Node3_Name
Stop-Node $Node2_Name
Stop-Node $Node1_Name

Write-Host "Cluster Stopped." -ForegroundColor Green

# Check Prerequisites

# --- PORTABLE MODE DETECTION ---
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$RepoRoot = Split-Path -Parent $ProjectRoot
$ToolsDir = Join-Path $RepoRoot "tools"

$ErlangHome = Join-Path $ToolsDir "erlang"
$RabbitHome = Join-Path $ToolsDir "rabbitmq"

if ((Test-Path "$ErlangHome\bin\erl.exe") -and (Test-Path "$RabbitHome\sbin\rabbitmq-server.bat")) {
    $env:ERLANG_HOME = $ErlangHome
    $env:RABBITMQ_HOME = $RabbitHome
    $env:PATH = "$ErlangHome\bin;$RabbitHome\sbin;$env:PATH"
    Write-Host "Portable Mode Detected in tools folder." -ForegroundColor Cyan
}

Write-Host "Checking for RabbitMQ and Erlang..."

$erl = Get-Command erl -ErrorAction SilentlyContinue
if ($erl) {
    Write-Host "Erlang found: $($erl.Source)" -ForegroundColor Green
} else {
    Write-Host "Erlang NOT found in PATH (and not in tools/erlang)" -ForegroundColor Red
}

$rmq = Get-Command rabbitmq-server.bat -ErrorAction SilentlyContinue
if ($rmq) {
    Write-Host "RabbitMQ Server found: $($rmq.Source)" -ForegroundColor Green
} else {
    Write-Host "RabbitMQ Server NOT found in PATH (and not in tools/rabbitmq)" -ForegroundColor Red
}

$ctl = Get-Command rabbitmqctl.bat -ErrorAction SilentlyContinue
if ($ctl) {
    Write-Host "RabbitMQ Ctl found: $($ctl.Source)" -ForegroundColor Green
} else {
    Write-Host "RabbitMQ Ctl NOT found in PATH" -ForegroundColor Red
}

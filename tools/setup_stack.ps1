# Setup-Stack.ps1
# Downloads and Configures Erlang and RabbitMQ in the tools directory
# Usage: Run this script to setup the environment

# FORCE TLS 1.2 (Required for GitHub)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ToolsDir = "D:\Github\sc_mqtt_rabbit_mq\tools"
# Updated URLs (direct links)
$ErlangUrl = "https://github.com/erlang/otp/releases/download/OTP-26.2.2/otp_win64_26.2.2.exe"
$RabbitUrl = "https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.13.0/rabbitmq-server-windows-3.13.0.zip"

Write-Host "Setting up RabbitMQ Stack in $ToolsDir..." -ForegroundColor Cyan

Import-Module BitsTransfer

# 1. Setup Erlang
$ErlangDir = Join-Path $ToolsDir "erlang"
# Cleanup partial install
if (Test-Path "$ErlangDir\bin\erl.exe") {
    Write-Host "Erlang check: Found bin\erl.exe"
}
else {
    Write-Host "Downloading Erlang 26.2.2..."
    $ErlangInstaller = Join-Path $ToolsDir "erlang_installer.exe"
    
    try {
        Start-BitsTransfer -Source $ErlangUrl -Destination $ErlangInstaller -ErrorAction Stop
    }
    catch {
        Write-Host "BITS Download Failed: $_" -ForegroundColor Red
        # Fallback to WebRequest with BasicParsing
        try {
            Invoke-WebRequest -Uri $ErlangUrl -OutFile $ErlangInstaller -UseBasicParsing
        }
        catch {
            Write-Host "All download methods failed for Erlang." -ForegroundColor Red
            exit 1
        }
    }
    
    if ((Get-Item $ErlangInstaller).Length -lt 1000000) {
        Write-Host "Error: Erlang installer is too small (download failed)." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Extracting Erlang (using 7z)..."
    $ErlangTemp = Join-Path $ToolsDir "erlang_temp"
    if (Test-Path $ErlangTemp) { Remove-Item $ErlangTemp -Recurse -Force }
    
    # 7z extraction
    & 7z x $ErlangInstaller -o"$ErlangTemp" -y | Out-Null
    
    # Check and Move
    if (Test-Path "$ErlangTemp\bin\erl.exe") {
        if (-not (Test-Path $ErlangDir)) { New-Item -ItemType Directory -Path $ErlangDir | Out-Null }
        Get-ChildItem "$ErlangTemp\*" | Move-Item -Destination $ErlangDir -Force
    }
    elseif (Test-Path "$ErlangTemp\otp_win64_26.2.2\bin\erl.exe") {
        if (-not (Test-Path $ErlangDir)) { New-Item -ItemType Directory -Path $ErlangDir | Out-Null }
        Get-ChildItem "$ErlangTemp\otp_win64_26.2.2\*" | Move-Item -Destination $ErlangDir -Force
    }
    else {
        # Fallback: just move everything from temp
        if (-not (Test-Path $ErlangDir)) { New-Item -ItemType Directory -Path $ErlangDir | Out-Null }
        Get-ChildItem "$ErlangTemp\*" | Move-Item -Destination $ErlangDir -Force
    }
    
    Remove-Item $ErlangTemp -Recurse -Force
    Remove-Item $ErlangInstaller -Force
    Write-Host "Erlang Installed." -ForegroundColor Green
}

# 2. Setup RabbitMQ
$RabbitDir = Join-Path $ToolsDir "rabbitmq"
if (Test-Path "$RabbitDir\sbin\rabbitmq-server.bat") {
    Write-Host "RabbitMQ check: Found sbin\rabbitmq-server.bat"
}
else {
    Write-Host "Downloading RabbitMQ 3.13.0..."
    $RabbitZip = Join-Path $ToolsDir "rabbitmq.zip"
    
    try {
        Start-BitsTransfer -Source $RabbitUrl -Destination $RabbitZip -ErrorAction Stop
    }
    catch {
        Write-Host "BITS Download Failed: $_" -ForegroundColor Red
        try {
            Invoke-WebRequest -Uri $RabbitUrl -OutFile $RabbitZip -UseBasicParsing
        }
        catch {
            Write-Host "All download methods failed for RabbitMQ." -ForegroundColor Red
            exit 1
        }
    }
    
    if ((Get-Item $RabbitZip).Length -lt 1000000) {
        Write-Host "Error: RabbitMQ zip is too small (download failed)." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Extracting RabbitMQ..."
    Expand-Archive -Path $RabbitZip -DestinationPath $ToolsDir -Force
    
    # Rename extracted folder
    $Extracted = Get-ChildItem -Path $ToolsDir -Filter "rabbitmq_server-*" | Select-Object -First 1
    if ($Extracted) {
        if (Test-Path $RabbitDir) { Remove-Item $RabbitDir -Recurse -Force }
        Rename-Item -Path $Extracted.FullName -NewName "rabbitmq"
    }
    
    Remove-Item $RabbitZip -Force
    Write-Host "RabbitMQ Installed." -ForegroundColor Green
}

Write-Host "Stack Setup Complete." -ForegroundColor Green

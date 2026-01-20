# Start-Mosquitto-Password.ps1
param($Port = 52345)

# Path to config file (absolute path to ensure it works from anywhere)
$ConfigFile = "d:\Github\sc_mqtt_mosquitto\mosquitto_password\ps1\mosquitto_password.conf"

Write-Host "Starting Mosquitto (password mode)..." -ForegroundColor Green
Write-Host "Using config: $ConfigFile" -ForegroundColor Gray

$running = Get-Process -Name "mosquitto" -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "Mosquitto already running. Stopping..." -ForegroundColor Yellow
    $running | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Check port usage (port is defined in config, but we check 52345 as default)
$portUsed = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
Where-Object { $_.State -eq "Listen" }
if ($portUsed) {
    Write-Host "Port $Port in use. Killing process..." -ForegroundColor Yellow
    Stop-Process -Id $portUsed.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Try to find mosquitto.exe
# Read .env for MOSQUITTO_DIR
$EnvFile = "d:\Github\sc_mqtt_mosquitto\.env"
$MosquittoDir = ""
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "MOSQUITTO_DIR=(.*)") {
            $MosquittoDir = $matches[1]
        }
    }
}

$MosquittoPath = "$MosquittoDir\mosquitto.exe"
if (-not (Test-Path $MosquittoPath)) {
    $MosquittoPath = "C:\Program Files\mosquitto\mosquitto.exe"
    if (-not (Test-Path $MosquittoPath)) {
        $MosquittoPath = "C:\Program Files (x86)\mosquitto\mosquitto.exe"
    }
}

if (Test-Path $MosquittoPath) {
    # We use -c to specify config file, and -p to specify port. -v for verbose logging.
    Start-Process -FilePath $MosquittoPath -ArgumentList "-c `"$ConfigFile`" -p $Port -v" -NoNewWindow
    Write-Host "Mosquitto (password mode) started." -ForegroundColor Green
    Write-Host "Credentials: admin / password123" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C in the console to stop" -ForegroundColor Yellow
}
else {
    Write-Host "Error: mosquitto.exe not found in standard locations." -ForegroundColor Red
}

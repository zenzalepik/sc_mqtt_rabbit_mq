# Start-Mosquitto.ps1
param($Port = 52345)

Write-Host "Starting Mosquitto on port $Port..." -ForegroundColor Green

# Cek jika sudah jalan
$running = Get-Process -Name "mosquitto" -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "Mosquitto already running. Stopping..." -ForegroundColor Yellow
    $running | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Cek port
$portUsed = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
Where-Object { $_.State -eq "Listen" }
if ($portUsed) {
    Write-Host "Port $Port in use. Killing process..." -ForegroundColor Yellow
    Stop-Process -Id $portUsed.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start mosquitto
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
    Start-Process -FilePath $MosquittoPath -ArgumentList "-p $Port -v" -NoNewWindow
    Write-Host "Mosquitto started on port $Port using $MosquittoPath" -ForegroundColor Green
    Write-Host "Press Ctrl+C in the console to stop" -ForegroundColor Yellow
} else {
    Write-Host "Error: mosquitto.exe not found." -ForegroundColor Red
}

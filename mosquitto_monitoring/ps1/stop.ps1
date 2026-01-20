# Stop-Mosquitto-Simple.ps1
param($Port = 52345)

Write-Host "=== MOSQUITTO CLEANER ===" -ForegroundColor Cyan

# 1. Stop service
Write-Host "`n[1] Stopping Mosquitto Service..." -ForegroundColor Yellow
Stop-Service -Name "mosquitto" -ErrorAction SilentlyContinue -Force
Write-Host "   Service stopped" -ForegroundColor Green

# 2. Kill processes
Write-Host "`n[2] Killing all Mosquitto processes..." -ForegroundColor Yellow
Get-Process -Name "mosquitto" -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "   All processes killed" -ForegroundColor Green

# 3. Check ports
$ports = @(1883, $Port)
foreach ($p in $ports) {
    Write-Host "`n[3] Checking port $p..." -ForegroundColor Yellow
    $connections = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
    if ($connections) {
        foreach ($conn in $connections) {
            $procId = $conn.OwningProcess
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "   Killing $($proc.ProcessName) (PID: $procId) using port $p" -ForegroundColor Red
                Stop-Process -Id $procId -Force
                Write-Host "   Process killed" -ForegroundColor Green
            }
        }
    }
    else {
        Write-Host "   Port $p is free" -ForegroundColor Green
    }
}

# 4. Final check
Write-Host "`n[4] Final check..." -ForegroundColor Cyan
$remaining = Get-Process -Name "mosquitto" -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "   WARNING: $($remaining.Count) process(es) still running" -ForegroundColor Red
}
else {
    Write-Host "   All clean!" -ForegroundColor Green
}

Write-Host "`n=== DONE ===" -ForegroundColor Cyan
pause
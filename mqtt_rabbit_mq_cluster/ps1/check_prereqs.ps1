# Check Prerequisites
Write-Host "Checking for RabbitMQ and Erlang..."

$erl = Get-Command erl -ErrorAction SilentlyContinue
if ($erl) {
    Write-Host "✓ Erlang found: $($erl.Source)" -ForegroundColor Green
}
else {
    Write-Host "✗ Erlang NOT found in PATH" -ForegroundColor Red
}

$rmq = Get-Command rabbitmq-server.bat -ErrorAction SilentlyContinue
if ($rmq) {
    Write-Host "✓ RabbitMQ Server found: $($rmq.Source)" -ForegroundColor Green
}
else {
    Write-Host "✗ RabbitMQ Server NOT found in PATH" -ForegroundColor Red
}

$ctl = Get-Command rabbitmqctl.bat -ErrorAction SilentlyContinue
if ($ctl) {
    Write-Host "✓ RabbitMQ Ctl found: $($ctl.Source)" -ForegroundColor Green
}
else {
    Write-Host "✗ RabbitMQ Ctl NOT found in PATH" -ForegroundColor Red
}

# PowerShell script to run Azurite and both Azure Functions apps

# Clean Azurite data
Write-Host "Cleaning Azurite data..."
if (Test-Path ".\azurite") {
    Remove-Item -Recurse -Force -Path ".\azurite\*"
}
else {
    New-Item -ItemType Directory -Path ".\azurite" | Out-Null
}


# Start Azurite
Write-Host "Starting Azurite..."
$azurite = Start-Process -PassThru -WindowStyle Hidden -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "azurite --location ./azurite --silent"
Start-Sleep -Seconds 2

# Start traffic_ingestor
Write-Host "Starting traffic_ingestor on port 7071..."
$ingestor = Start-Process -PassThru -WindowStyle Hidden -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd traffic_ingestor; func start --port 7071"
Start-Sleep -Seconds 2

# Start traffic_refresher on port 7072
Write-Host "Starting traffic_refresher on port 7072..."
$refresher = Start-Process -PassThru -WindowStyle Hidden -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd traffic_refresher; func start --port 7072"

# Wait for user to press Ctrl+C
Write-Host "`n All services running. Press Ctrl+C to stop."

# Trap Ctrl+C and clean up
$event = Register-EngineEvent PowerShell.Exiting -Action {
    Write-Host "`n🧹 Shutting down all services..."
    if ($refresher) { Stop-Process -Id $refresher.Id -Force }
    if ($ingestor) { Stop-Process -Id $ingestor.Id -Force }
    if ($azurite) { Stop-Process -Id $azurite.Id -Force }
    Write-Host "✅ All services stopped."
}

# Keep script alive
while ($true) {
    Start-Sleep -Seconds 1
}

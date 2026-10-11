# Stop all running Options Recommender server processes cleanly
$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host "           STOPPING OPTIONS SUGGESTER SERVERS                    " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host ""

function Kill-PortProcess([int]$port, [string]$name) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($conns) {
            foreach ($conn in $conns) {
                $pidToKill = $conn.OwningProcess
                if ($pidToKill -and $pidToKill -gt 4) {
                    Write-Host "Stopping $name (Port $port, PID $pidToKill)..." -ForegroundColor Yellow
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                }
            }
            Write-Host "[OK] Port $port freed." -ForegroundColor Green
        } else {
            Write-Host "[OK] Port $port is already inactive." -ForegroundColor Gray
        }
    } catch {
        Write-Host "Could not query port $port." -ForegroundColor Gray
    }
}

Kill-PortProcess 8000 "FastAPI Backend"
Kill-PortProcess 3000 "Next.js Frontend"

Write-Host ""
Write-Host "All servers stopped successfully." -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host ""
Start-Sleep -Seconds 2

# Options Suggester Pro - High Reliability Launcher
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "          OPTIONS SUGGESTER PRO - 1-CLICK LAUNCHER               " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = Split-Path -Parent $PSScriptRoot
if (-not $rootDir) { $rootDir = Get-Location }

# Function to check if a web endpoint is responding
function Test-HttpEndpoint([string]$url, [int]$timeoutSec = 2) {
    try {
        $req = [System.Net.WebRequest]::Create($url)
        $req.Timeout = $timeoutSec * 1000
        $res = $req.GetResponse()
        $statusCode = [int]$res.StatusCode
        $res.Close()
        return ($statusCode -ge 200 -and $statusCode -lt 400)
    } catch {
        return $false
    }
}

# Function to get PID on a port
function Get-PidOnPort([int]$port) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($conn) { return $conn.OwningProcess }
    } catch {}
    return $null
}

# ----------------- 1. BACKEND (PORT 8000) -----------------
Write-Host "[1/3] Checking Backend API on http://127.0.0.1:8000..." -ForegroundColor White
$backendRunning = Test-HttpEndpoint "http://127.0.0.1:8000/api/health"

if ($backendRunning) {
    Write-Host "  -> Backend is already healthy and responding!" -ForegroundColor Green
} else {
    $existingPid = Get-PidOnPort 8000
    if ($existingPid) {
        Write-Host "  -> Port 8000 is occupied by PID $existingPid but not responding. Freeing port..." -ForegroundColor Yellow
        Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
    
    Write-Host "  -> Starting FastAPI Backend (.venv uvicorn)..." -ForegroundColor Cyan
    $pyExe = Join-Path $rootDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $pyExe)) { $pyExe = "python.exe" }
    
    # Spawn independent detached process using Windows cmd start
    $backendCmd = "cd /d `"$rootDir`" && start `"Options-Backend-8000`" /min `"$pyExe`" -m uvicorn api:app --host 127.0.0.1 --port 8000"
    cmd.exe /c $backendCmd
    
    # Wait for backend to be ready
    $retries = 0
    while (-not (Test-HttpEndpoint "http://127.0.0.1:8000/api/health") -and $retries -lt 20) {
        Start-Sleep -Milliseconds 600
        $retries++
    }
    if (Test-HttpEndpoint "http://127.0.0.1:8000/api/health") {
        Write-Host "  -> Backend online and ready!" -ForegroundColor Green
    } else {
        Write-Host "  -> Backend starting in background..." -ForegroundColor Yellow
    }
}

# ----------------- 2. FRONTEND (PORT 3000) -----------------
Write-Host "[2/3] Checking Next.js Frontend on http://localhost:3000..." -ForegroundColor White
$frontendRunning = Test-HttpEndpoint "http://localhost:3000"

if ($frontendRunning) {
    Write-Host "  -> Frontend is already healthy and responding!" -ForegroundColor Green
} else {
    $existingPid = Get-PidOnPort 3000
    if ($existingPid) {
        Write-Host "  -> Port 3000 is occupied by PID $existingPid but not responding. Freeing port..." -ForegroundColor Yellow
        Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }

    Write-Host "  -> Starting Next.js Web Server (npm run dev)..." -ForegroundColor Cyan
    $frontendDir = Join-Path $rootDir "frontend"
    
    # Spawn independent detached process using Windows cmd start
    $frontendCmd = "cd /d `"$frontendDir`" && start `"Options-Frontend-3000`" /min cmd.exe /c npm.cmd run dev"
    cmd.exe /c $frontendCmd

    # Wait for frontend to be ready
    $retries = 0
    while (-not (Test-HttpEndpoint "http://localhost:3000") -and $retries -lt 25) {
        Start-Sleep -Milliseconds 800
        $retries++
    }
    if (Test-HttpEndpoint "http://localhost:3000") {
        Write-Host "  -> Frontend online and ready!" -ForegroundColor Green
    } else {
        Write-Host "  -> Frontend initializing in background..." -ForegroundColor Yellow
    }
}

# ----------------- 3. OPEN BROWSER -----------------
Write-Host "[3/3] Launching web browser..." -ForegroundColor White
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "                   APPLICATION READY!                            " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "  * Web Application : http://localhost:3000" -ForegroundColor Cyan
Write-Host "  * REST API & Docs : http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  * Paper Portfolio : Tab 'Paper Portfolio' or press key '9'" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tip: To stop the servers later, simply double-click stop.bat" -ForegroundColor Gray
Write-Host "==================================================================" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 2

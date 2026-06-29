#Requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$FrontendDir = if ($env:FRONTEND_DIR) { $env:FRONTEND_DIR } else { "src/web" }
$BackendDir = if ($env:BACKEND_DIR) { $env:BACKEND_DIR } else { "src/api" }
$FrontendCmd = if ($env:FRONTEND_CMD) { $env:FRONTEND_CMD } else { "npm run dev" }
$BackendCmd = if ($env:BACKEND_CMD) { $env:BACKEND_CMD } else { "npm run dev" }
$FrontendUrl = if ($env:FRONTEND_URL) { $env:FRONTEND_URL } else { "http://localhost:3000" }

$FrontendPath = Join-Path $RootDir $FrontendDir
$BackendPath = Join-Path $RootDir $BackendDir

if (-not (Test-Path $FrontendPath)) {
    throw "Frontend directory not found: $FrontendPath"
}

if (-not (Test-Path $BackendPath)) {
    throw "Backend directory not found: $BackendPath"
}

if (-not (Test-Path (Join-Path $FrontendPath "package.json"))) {
    throw "Missing package.json in frontend directory: $FrontendPath"
}

if (-not (Test-Path (Join-Path $BackendPath "package.json"))) {
    throw "Missing package.json in backend directory: $BackendPath"
}

Write-Host "Starting backend: $BackendCmd ($BackendDir)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location -LiteralPath '$BackendPath'; $BackendCmd"

Write-Host "Starting frontend: $FrontendCmd ($FrontendDir)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location -LiteralPath '$FrontendPath'; $FrontendCmd"

Start-Sleep -Seconds 2
Start-Process $FrontendUrl

Write-Host "Frontend URL: $FrontendUrl" -ForegroundColor Green
Write-Host "Frontend/backend started in new PowerShell windows." -ForegroundColor Green

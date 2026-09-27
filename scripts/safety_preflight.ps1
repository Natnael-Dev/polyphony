# Safety Preflight Check for Polyphony Dark Factory
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🛡️  RUNNING POLYPHONY SAFETY PREFLIGHT CHECKS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Verify secrets.json exists
Write-Host "[1/3] Checking seat credentials (secrets.json)..." -NoNewline
if (-not (Test-Path "secrets.json")) {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "❌ secrets.json is missing! Please run scripts/provision_seats.py or restore credentials." -ForegroundColor Red
    exit 1
}
Write-Host " OK" -ForegroundColor Green

# 2. Verify turn_timeout_s=900 in band/run_developer.py
Write-Host "[2/3] Checking developer adapter turn timeout (900s)..." -NoNewline
$devAdapter = "band/run_developer.py"
if (-not (Test-Path $devAdapter)) {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "❌ $devAdapter not found!" -ForegroundColor Red
    exit 1
}
$content = Get-Content $devAdapter -Raw
if ($content -notmatch "turn_timeout_s\s*=\s*900") {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "❌ $devAdapter does not have turn_timeout_s=900 configured!" -ForegroundColor Red
    exit 1
}
Write-Host " OK" -ForegroundColor Green

# 3. Check git status
Write-Host "[3/3] Checking Git working tree hygiene..." -NoNewline
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "⚠️ WORKING TREE DIRTY. Commit or stash changes before launching the factory to ensure the Git Time Machine is armed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Dirty items:" -ForegroundColor DarkGray
    $gitStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    exit 1
}
Write-Host " OK" -ForegroundColor Green

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "✅ SAFETY PREFLIGHT PASSED: Git clean, 900s timeout active, credentials verified." -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
exit 0

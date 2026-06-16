param([switch]$Force)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$DataDir = Join-Path $Root "data"
$PidPath = Join-Path $DataDir "continuous_agent.pid"
$StopPath = Join-Path $DataDir "continuous_agent.stop"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
Set-Content -Path $StopPath -Value ([DateTime]::UtcNow.ToString("o")) -Encoding ASCII

if (!(Test-Path $PidPath)) {
    Write-Output "Stop requested. No PID file is present."
    exit 0
}

$pidText = Get-Content $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1
$pidValue = 0
if (![int]::TryParse($pidText, [ref]$pidValue)) {
    Write-Output "Stop requested. PID file is not parseable."
    exit 0
}

$process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
if (!$process) {
    Write-Output "Stop requested. Process $pidValue is not running."
    exit 0
}

if ($Force) {
    Stop-Process -Id $pidValue -Force
    Write-Output "Force-stopped continuous runner process $pidValue."
} else {
    Write-Output "Stop requested for continuous runner process $pidValue. It will exit after the current mode or sleep interval."
}

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$DataDir = Join-Path $Root "data"
$PidPath = Join-Path $DataDir "continuous_agent.pid"
$StatusPath = Join-Path $DataDir "continuous_agent_status.json"

$pidValue = $null
$processRunning = $false
if (Test-Path $PidPath) {
    $pidText = Get-Content $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1
    $parsedPid = 0
    if ([int]::TryParse($pidText, [ref]$parsedPid)) {
        $pidValue = $parsedPid
        $processRunning = [bool](Get-Process -Id $parsedPid -ErrorAction SilentlyContinue)
    }
}

$status = [ordered]@{
    process_running = $processRunning
    pid = $pidValue
    status_file = $StatusPath
    status = $null
}

if (Test-Path $StatusPath) {
    $status.status = Get-Content $StatusPath -Raw | ConvertFrom-Json
}

$status | ConvertTo-Json -Depth 6

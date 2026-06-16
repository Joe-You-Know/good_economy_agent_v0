param(
    [int]$IntervalSeconds = 900,
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$DataDir = Join-Path $Root "data"
$PidPath = Join-Path $DataDir "continuous_agent.pid"
$Runner = Join-Path $PSScriptRoot "run_continuous_agent.ps1"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

if (Test-Path $PidPath) {
    $pidText = Get-Content $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1
    $pidValue = 0
    if ([int]::TryParse($pidText, [ref]$pidValue)) {
        $existing = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Output "Continuous Good Economy Agent already running with PID $pidValue."
            exit 0
        }
    }
    Remove-Item -Path $PidPath -ErrorAction SilentlyContinue
}

$argList = "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" -IntervalSeconds $IntervalSeconds"
if ($PythonExe) {
    $argList += " -PythonExe `"$PythonExe`""
}

$process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList $argList `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -PassThru

Write-Output "Started continuous Good Economy Agent with PID $($process.Id)."

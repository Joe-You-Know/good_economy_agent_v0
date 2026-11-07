param(
    [int]$IntervalSeconds = 900,
    [string]$PythonExe = "",
    [string]$ConfigPath = "config.json"
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogDir = Join-Path $Root "logs"
$DataDir = Join-Path $Root "data"
$LogPath = Join-Path $LogDir "continuous_agent.log"
$PidPath = Join-Path $DataDir "continuous_agent.pid"
$StatusPath = Join-Path $DataDir "continuous_agent_status.json"
$StopPath = Join-Path $DataDir "continuous_agent.stop"
$KillSwitchPath = Join-Path $Root "KILL_SWITCH"
$ApprovalDir = Join-Path $Root "outputs\approval_requests"

New-Item -ItemType Directory -Force -Path $LogDir, $DataDir | Out-Null

function Get-UtcNow {
    return [DateTime]::UtcNow.ToString("o")
}

function Write-AgentLog {
    param([string]$Message)
    Add-Content -Path $LogPath -Value ("[{0}] {1}" -f (Get-UtcNow), $Message)
}

function Write-AgentStatus {
    param(
        [string]$State,
        [string]$Message,
        [int]$Cycle = 0,
        [string]$Mode = "",
        [int]$ExitCode = 0
    )

    $status = [ordered]@{
        timestamp_utc = Get-UtcNow
        state = $State
        message = $Message
        pid = $PID
        cycle = $Cycle
        mode = $Mode
        last_exit_code = $ExitCode
        interval_seconds = $IntervalSeconds
        kill_switch_triggered = (Test-Path $KillSwitchPath)
        external_write_actions = "disabled"
        stop_file = $StopPath
        log_file = $LogPath
    }
    $status | ConvertTo-Json -Depth 4 | Set-Content -Path $StatusPath -Encoding UTF8
}

function Resolve-Python {
    if ($PythonExe) {
        return $PythonExe
    }
    $Bundled = "C:\Users\josep\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $Bundled) {
        return $Bundled
    }
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if ($Python) {
        return $Python.Source
    }
    $Py = Get-Command py -ErrorAction SilentlyContinue
    if ($Py) {
        return $Py.Source
    }
    throw "No Python executable found. Pass -PythonExe explicitly."
}

function Test-ExistingRunner {
    if (!(Test-Path $PidPath)) {
        return $false
    }
    $existingPidText = (Get-Content $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1)
    $existingPid = 0
    if (![int]::TryParse($existingPidText, [ref]$existingPid)) {
        return $false
    }
    try {
        $process = Get-Process -Id $existingPid -ErrorAction Stop
        return $process.Id -ne $PID
    } catch {
        return $false
    }
}

function Write-ApprovalRequest {
    param(
        [string]$Kind,
        [string]$Summary,
        [string]$RequestedAction,
        [string]$EvidencePath = "",
        [string]$RiskNote = ""
    )

    New-Item -ItemType Directory -Force -Path $ApprovalDir | Out-Null
    $request = [ordered]@{
        timestamp_utc = Get-UtcNow
        status = "pending"
        kind = $Kind
        summary = $Summary
        requested_action = $RequestedAction
        evidence_path = $EvidencePath
        risk_note = $RiskNote
        external_write_action = $true
        requires_fresh_user_approval = $true
    }
    $jsonPath = Join-Path $ApprovalDir "latest.json"
    $mdPath = Join-Path $ApprovalDir "latest.md"
    $request | ConvertTo-Json -Depth 5 | Set-Content -Path $jsonPath -Encoding UTF8
    @"
# Pending Approval Request

Generated: $($request.timestamp_utc)

## Summary

$Summary

## Requested Action

$RequestedAction

## Evidence

$EvidencePath

## Risk Note

$RiskNote
"@ | Set-Content -Path $mdPath -Encoding UTF8
    Write-AgentLog "Approval request written: $Kind"
}

function Check-SupervisedWorkApprovalNeed {
    $decisionPath = Join-Path $Root "outputs\supervised_work_decision.json"
    if (!(Test-Path $decisionPath)) {
        return
    }
    try {
        $decision = Get-Content $decisionPath -Raw | ConvertFrom-Json
    } catch {
        Write-AgentLog "Could not parse supervised work decision for approval need."
        return
    }
    if ($decision.status -eq "local_work_package_prepared") {
        $candidate = $decision.selected_candidate
        $summary = "Good Economy Agent prepared local earned-income work for: $($candidate.title)"
        $requested = "Review the work package and approve or deny the next external write action: $($decision.next_autonomous_step)"
        $evidence = ""
        if ($decision.work_package -and $decision.work_package.markdown) {
            $evidence = $decision.work_package.markdown
        }
        Write-ApprovalRequest `
            -Kind "external_write_review" `
            -Summary $summary `
            -RequestedAction $requested `
            -EvidencePath $evidence `
            -RiskNote "The runner will not publish, submit, message, invoice, or collect payment without approval."
    }
}

if (Test-ExistingRunner) {
    Write-AgentStatus -State "already_running" -Message "A continuous Good Economy Agent runner is already active."
    Write-AgentLog "Refused to start duplicate runner."
    exit 0
}

Set-Content -Path $PidPath -Value $PID -Encoding ASCII
Remove-Item -Path $StopPath -ErrorAction SilentlyContinue

$ResolvedPython = Resolve-Python
$cycle = 0
Write-AgentLog "Continuous Good Economy Agent runner started. PID=$PID interval_seconds=$IntervalSeconds"
Write-AgentStatus -State "running" -Message "Continuous runner started." -Cycle $cycle

try {
    while ($true) {
        if (Test-Path $StopPath) {
            Write-AgentStatus -State "stopped" -Message "Stop file detected before cycle start." -Cycle $cycle
            Write-AgentLog "Stop file detected before cycle start."
            break
        }

        $cycle += 1
        Write-AgentLog "Cycle $cycle started."
        Write-AgentStatus -State "running" -Message "Cycle $cycle started." -Cycle $cycle

        $modes = @("live-preflight", "monitor", "asset-discovery", "asset-work")
        if (!(Test-Path $KillSwitchPath)) {
            $modes += @("live-discovery", "supervised-work")
        } else {
            Write-AgentLog "Kill switch active; skipping live-discovery and supervised-work."
        }

        foreach ($mode in $modes) {
            if (Test-Path $StopPath) {
                Write-AgentStatus -State "stopping" -Message "Stop file detected." -Cycle $cycle -Mode $mode
                break
            }

            Write-AgentLog "Running mode: $mode"
            Write-AgentStatus -State "running" -Message "Running mode $mode." -Cycle $cycle -Mode $mode
            Push-Location $Root
            try {
                $commandOutput = & $ResolvedPython "run_agent.py" "--config" $ConfigPath "--mode" $mode 2>&1
                $exitCode = $LASTEXITCODE
            } finally {
                Pop-Location
            }

            if ($null -eq $exitCode) {
                $exitCode = 0
            }
            foreach ($line in $commandOutput) {
                Add-Content -Path $LogPath -Value ([string]$line)
            }
            Write-AgentStatus -State "running" -Message "Completed mode $mode." -Cycle $cycle -Mode $mode -ExitCode $exitCode
            Write-AgentLog "Completed mode: $mode exit_code=$exitCode"
            if ($mode -eq "supervised-work") {
                Check-SupervisedWorkApprovalNeed
            }
        }

        if (Test-Path $StopPath) {
            Write-AgentStatus -State "stopped" -Message "Stop file detected after cycle." -Cycle $cycle
            Write-AgentLog "Stop file detected after cycle."
            break
        }

        Write-AgentStatus -State "sleeping" -Message "Cycle $cycle complete; sleeping." -Cycle $cycle
        Write-AgentLog "Cycle $cycle complete. Sleeping for $IntervalSeconds seconds."
        Start-Sleep -Seconds $IntervalSeconds
    }
} catch {
    Write-AgentStatus -State "error" -Message $_.Exception.Message -Cycle $cycle
    Write-AgentLog ("ERROR: " + $_.Exception.Message)
    throw
} finally {
    if (Test-Path $PidPath) {
        $pidText = Get-Content $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($pidText -eq [string]$PID) {
            Remove-Item -Path $PidPath -ErrorAction SilentlyContinue
        }
    }
    Write-AgentLog "Continuous Good Economy Agent runner exited."
}

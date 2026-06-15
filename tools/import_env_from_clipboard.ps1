param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "OPENAI_API_KEY",
        "GITHUB_TOKEN",
        "COURTLISTENER_TOKEN",
        "OPENLAWS_API_KEY",
        "PAYMENT_PROVIDER_API_KEY",
        "DONATION_URL",
        "SPONSORSHIP_URL",
        "OPENLAWS_API_BASE_URL"
    )]
    [string] $Key
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$EnvPath = Join-Path $Root ".env"
$Value = (Get-Clipboard -Raw).Trim()

if ([string]::IsNullOrWhiteSpace($Value)) {
    throw "Clipboard is empty. Copy the value first, then rerun this helper."
}

if ($Value -match "[`r`n]") {
    throw "Clipboard contains multiple lines. Refusing to import it as a single env value."
}

if (-not (Test-Path -LiteralPath $EnvPath)) {
    New-Item -ItemType File -Path $EnvPath -Force | Out-Null
}

$Lines = @(Get-Content -LiteralPath $EnvPath)
$Pattern = "^\s*$([regex]::Escape($Key))="
$Updated = $false

for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i] -match $Pattern) {
        $Lines[$i] = "$Key=$Value"
        $Updated = $true
        break
    }
}

if (-not $Updated) {
    $Lines += "$Key=$Value"
}

Set-Content -LiteralPath $EnvPath -Value $Lines -Encoding UTF8
Write-Output "Updated $Key from clipboard. Value redacted."

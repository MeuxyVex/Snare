# Install Snare from this checkout. Use -WithVolatility to install Volatility 3.
[CmdletBinding()]
param(
    [switch]$WithVolatility
)

$ErrorActionPreference = 'Stop'
$uv = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue
if (-not $uv) {
    throw 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/'
}

& $uv.Source --directory $PSScriptRoot sync --locked
if ($LASTEXITCODE -ne 0) {
    throw "Snare dependency installation failed (uv exit code $LASTEXITCODE)."
}

& $uv.Source --directory $PSScriptRoot run --locked --no-sync snare --version
if ($LASTEXITCODE -ne 0) {
    throw "The Snare CLI could not start (exit code $LASTEXITCODE)."
}

$config = Join-Path $PSScriptRoot 'snare.toml'
if (-not (Test-Path -LiteralPath $config -PathType Leaf)) {
    $example = Join-Path $PSScriptRoot 'snare.example.toml'
    [System.IO.File]::Copy($example, $config)
    Write-Host "Created $config"
}

if ($WithVolatility) {
    & $uv.Source tool install --link-mode copy --python 3.12 volatility3
    if ($LASTEXITCODE -ne 0) {
        throw "Volatility 3 installation failed (uv exit code $LASTEXITCODE)."
    }
    if (-not (Get-Command vol -CommandType Application -ErrorAction SilentlyContinue)) {
        Write-Host 'To enable vol on PATH, run uv tool update-shell and reopen PowerShell.'
    }
}

Write-Host 'Snare is installed. From the checkout, run uv run snare config check to check external tools.'
Write-Host 'See the README for MemProcFS, Zeek and Suricata setup on the analysis host.'

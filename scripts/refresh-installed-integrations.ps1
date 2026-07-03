# Refresh Installed Integrations (Refactored)
# Uses shared helper functions.

param(
    [ValidateSet('Antigravity', 'Codex', 'All')]
    [string]$Target = 'All',

    [string]$CodexRepoPath,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# Import shared helpers
$helpersPath = Join-Path $PSScriptRoot 'helpers.ps1'
if (Test-Path $helpersPath) {
    . $helpersPath
}

$Root = Get-ProjectRoot
$structureValidator = Join-Path $Root 'scripts\validate-structure.ps1'
$manifestValidator = Join-Path $Root 'scripts\validate-manifest.ps1'
$codexExporter = Join-Path $Root 'adapters\codex\export-codex-skills.ps1'
$codexValidator = Join-Path $Root 'adapters\codex\validate_codex_export.py'
$codexInstaller = Join-Path $Root 'adapters\codex\install-to-repo.ps1'
$pluginUrl = 'https://github.com/Baelfyre/Orchestra'

function Invoke-RequiredCommand {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    Write-ColorHost 'INFO' "> $Command $($Arguments -join ' ')"
    & $Command @Arguments

    if (-not $?) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

function Invoke-PreRefreshValidation {
    Write-ColorHost 'INFO' "Running pre-refresh validation..."

    if (-not (Test-Path -LiteralPath $structureValidator -PathType Leaf)) {
        throw "Missing validator: $structureValidator"
    }

    if (-not (Test-Path -LiteralPath $manifestValidator -PathType Leaf)) {
        throw "Missing validator: $manifestValidator"
    }

    $psExe = (Get-Process -Id $PID).Path
    & $psExe -ExecutionPolicy Bypass -File $structureValidator
    if (-not $?) {
        throw "Structure validation failed."
    }

    & $psExe -ExecutionPolicy Bypass -File $manifestValidator
    if (-not $?) {
        throw "Manifest validation failed."
    }

    Write-ColorHost 'SUCCESS' "Pre-refresh validation passed."
}

function Refresh-Antigravity {
    Write-ColorHost 'INFO' "Refreshing Antigravity plugin..."

    try {
        & agy plugin uninstall 'amalgam-conductor'
        Write-ColorHost 'SUCCESS' "Existing legacy Antigravity plugin uninstalled."
    }
    catch {
        Write-ColorHost 'WARNING' "Legacy uninstall failed or plugin was not installed."
    }

    try {
        & agy plugin uninstall 'conductor'
        Write-ColorHost 'SUCCESS' "Existing Antigravity Conductor plugin uninstalled."
    }
    catch {
        Write-ColorHost 'WARNING' "Uninstall failed or plugin was not installed. Continuing with install."
    }

    Invoke-RequiredCommand -Command 'agy' -Arguments @('plugin', 'install', $pluginUrl)
    Invoke-RequiredCommand -Command 'agy' -Arguments @('plugin', 'list')

    Write-ColorHost 'SUCCESS' "Antigravity refresh complete."
}

function Refresh-Codex {
    if ([string]::IsNullOrWhiteSpace($CodexRepoPath)) {
        throw "Codex refresh requires -CodexRepoPath."
    }

    if (-not (Test-Path -LiteralPath $CodexRepoPath -PathType Container)) {
        throw "Codex repo path not found: $CodexRepoPath"
    }

    if (-not (Test-Path -LiteralPath $codexInstaller -PathType Leaf)) {
        throw "Codex installer not found: $codexInstaller"
    }

    if (-not (Test-Path -LiteralPath $codexExporter -PathType Leaf)) {
        throw "Codex exporter not found: $codexExporter"
    }

    if (-not (Test-Path -LiteralPath $codexValidator -PathType Leaf)) {
        throw "Codex export validator not found: $codexValidator"
    }

    Write-ColorHost 'INFO' "Refreshing Codex skills into: $CodexRepoPath"

    $psExe = (Get-Process -Id $PID).Path
    Invoke-RequiredCommand -Command $psExe -Arguments @('-ExecutionPolicy', 'Bypass', '-File', $codexExporter)

    $pythonExe = (Get-Command python -ErrorAction Stop).Source
    Invoke-RequiredCommand -Command $pythonExe -Arguments @($codexValidator)

    $args = @('-ExecutionPolicy', 'Bypass', '-File', $codexInstaller, '-TargetRepo', $CodexRepoPath)
    if ($Force) {
        $args += '-Force'
    }

    Invoke-RequiredCommand -Command $psExe -Arguments $args

    Write-ColorHost 'SUCCESS' "Codex refresh complete."
}

Invoke-PreRefreshValidation

switch ($Target) {
    'Antigravity' {
        Refresh-Antigravity
    }

    'Codex' {
        Refresh-Codex
    }

    'All' {
        Refresh-Antigravity
        Refresh-Codex
    }
}

Write-ColorHost 'SUCCESS' "Refresh complete for target: $Target"

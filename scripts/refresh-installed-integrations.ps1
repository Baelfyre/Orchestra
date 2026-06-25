param(
    [ValidateSet('Antigravity', 'Codex', 'All')]
    [string]$Target = 'All',

    [string]$CodexRepoPath,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$structureValidator = Join-Path $Root 'scripts\validate-structure.ps1'
$manifestValidator = Join-Path $Root 'scripts\validate-manifest.ps1'
$codexInstaller = Join-Path $Root 'adapters\codex\install-to-repo.ps1'
$pluginUrl = 'https://github.com/Baelfyre/Orchestra'
$pluginName = 'amalgam-conductor'

function Invoke-RequiredCommand {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    Write-Output "> $Command $($Arguments -join ' ')"
    & $Command @Arguments

    if (-not $?) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

function Invoke-PreRefreshValidation {
    Write-Output "Running pre-refresh validation..."

    if (-not (Test-Path -LiteralPath $structureValidator -PathType Leaf)) {
        throw "Missing validator: $structureValidator"
    }

    if (-not (Test-Path -LiteralPath $manifestValidator -PathType Leaf)) {
        throw "Missing validator: $manifestValidator"
    }

    & powershell -ExecutionPolicy Bypass -File $structureValidator
    if (-not $?) {
        throw "Structure validation failed."
    }

    & powershell -ExecutionPolicy Bypass -File $manifestValidator
    if (-not $?) {
        throw "Manifest validation failed."
    }

    Write-Output "Pre-refresh validation passed."
}

function Refresh-Antigravity {
    Write-Output "Refreshing Antigravity plugin..."

    try {
        & agy plugin uninstall $pluginName
        Write-Output "Existing Antigravity plugin uninstalled."
    }
    catch {
        Write-Warning "Uninstall failed or plugin was not installed. Continuing with install."
    }

    Invoke-RequiredCommand -Command 'agy' -Arguments @('plugin', 'install', $pluginUrl)
    Invoke-RequiredCommand -Command 'agy' -Arguments @('plugin', 'list')

    Write-Output "Antigravity refresh complete."
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

    Write-Output "Refreshing Codex skills into: $CodexRepoPath"

    $args = @('-ExecutionPolicy', 'Bypass', '-File', $codexInstaller, '-TargetRepo', $CodexRepoPath)
    if ($Force) {
        $args += '-Force'
    }

    Invoke-RequiredCommand -Command 'powershell' -Arguments $args

    Write-Output "Codex refresh complete."
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

Write-Output "Refresh complete for target: $Target"
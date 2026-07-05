# Refresh Installed Integrations (Refactored)
# Uses shared helper functions.

param(
    [ValidateSet('Antigravity', 'Codex', 'All')]
    [string]$Target = 'Codex',

    [string]$CodexRepoPath,

    [string]$GlobalCodexSkillsPath = "$HOME\.codex\skills",

    [switch]$Force,

    [switch]$KeepTempExport
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
    $resolvedCodexRepoPath = $CodexRepoPath
    if ([string]::IsNullOrWhiteSpace($resolvedCodexRepoPath)) {
        $resolvedCodexRepoPath = $Root
    }

    if (-not (Test-Path -LiteralPath $resolvedCodexRepoPath -PathType Container)) {
        throw "Codex repo path not found: $resolvedCodexRepoPath"
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

    if ([string]::IsNullOrWhiteSpace($GlobalCodexSkillsPath)) {
        throw "Global Codex skills path is required."
    }

    if (-not (Test-Path -LiteralPath $GlobalCodexSkillsPath -PathType Container)) {
        New-Item -ItemType Directory -Path $GlobalCodexSkillsPath -Force | Out-Null
    }

    Write-ColorHost 'INFO' "Refreshing Codex skills into repo-local and global runtime locations..."

    $psExe = (Get-Process -Id $PID).Path
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
    $tempExportRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("orchestra-runtime-export-" + [System.Guid]::NewGuid().ToString("N"))
    $tempDeleted = $false

    try {
        New-Item -ItemType Directory -Path $tempExportRoot -Force | Out-Null
        Write-ColorHost 'INFO' "Temporary export staging: $tempExportRoot"

        Invoke-RequiredCommand -Command $psExe -Arguments @(
            '-ExecutionPolicy', 'Bypass', '-File', $codexExporter,
            '-TargetRoot', $tempExportRoot
        )
        Invoke-RequiredCommand -Command $pythonExe -Arguments @(
            $codexValidator, '--export-root', $tempExportRoot
        )

        $stagedSkillsDir = Join-Path $tempExportRoot 'skills'
        $localSkillsDir = Join-Path $resolvedCodexRepoPath '.agents\skills'

        Invoke-RequiredCommand -Command $psExe -Arguments @(
            '-ExecutionPolicy', 'Bypass', '-File', $codexInstaller,
            '-TargetRepo', $resolvedCodexRepoPath,
            '-SourceSkillsDir', $stagedSkillsDir,
            '-Force'
        )

        Copy-SkillTree -SourceSkillsDir $stagedSkillsDir -DestinationSkillsDir $GlobalCodexSkillsPath | Out-Host

        $localParityIssues = Compare-DirectoryParity -SourceRoot $stagedSkillsDir -DestinationRoot $localSkillsDir
        if ($localParityIssues.Count -gt 0) {
            $localParityIssues | ForEach-Object { Write-ColorHost 'ERROR' $_ }
            throw "Repo-local Codex runtime parity check failed."
        }
        Write-ColorHost 'SUCCESS' "Repo-local Codex runtime parity: MATCH"

        $globalStageCompare = Join-Path $tempExportRoot 'global-compare'
        New-Item -ItemType Directory -Path $globalStageCompare -Force | Out-Null
        Get-ChildItem -LiteralPath $stagedSkillsDir -Directory | ForEach-Object {
            Copy-Item -LiteralPath (Join-Path $GlobalCodexSkillsPath $_.Name) -Destination (Join-Path $globalStageCompare $_.Name) -Recurse -Force
        }

        $globalParityIssues = Compare-DirectoryParity -SourceRoot $stagedSkillsDir -DestinationRoot $globalStageCompare
        if ($globalParityIssues.Count -gt 0) {
            $globalParityIssues | ForEach-Object { Write-ColorHost 'ERROR' $_ }
            throw "Global Codex runtime parity check failed."
        }
        Write-ColorHost 'SUCCESS' "Global Codex runtime parity: MATCH"

        if ($KeepTempExport) {
            Write-ColorHost 'INFO' "Temporary export preserved at: $tempExportRoot"
        }
        else {
            Remove-Item -LiteralPath $tempExportRoot -Recurse -Force
            $tempDeleted = $true
            Write-ColorHost 'SUCCESS' "Temporary export deleted."
        }

        Write-ColorHost 'SUCCESS' "Codex refresh complete."
    }
    finally {
        if (-not $KeepTempExport -and -not $tempDeleted -and (Test-Path -LiteralPath $tempExportRoot -PathType Container)) {
            Remove-Item -LiteralPath $tempExportRoot -Recurse -Force
        }
    }
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

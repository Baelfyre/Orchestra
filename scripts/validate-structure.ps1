# Re-architected Structure Validator Script
# Uses single source of truth (plugin.json) for active skills and commands, and shared helper functions.

param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

# Import shared helpers
$helpersPath = Join-Path $PSScriptRoot 'helpers.ps1'
if (-not (Test-Path $helpersPath)) {
    Write-Error "Helpers module missing at: $helpersPath"
    exit 1
}
. $helpersPath

$requiredRoot = @(
    'README.md',
    'CHANGELOG.md',
    'LICENSE',
    'plugin.json',
    'AGENTS.md',
    'ROUTING_MAP.md',
    'SKILL_INDEX.md',
    'docs/CONTRIBUTING.md',
    'docs/meta/CHANGELOG.md',
    'docs/meta/DISCLAIMER.md',
    'docs/project/FOUNDATION.md',
    'docs/project/ROADMAP.md',
    'docs/project/PLUGIN_READINESS.md',
    'docs/project/MANIFEST_SCHEMA.md',
    'docs/project/V1_READINESS_CHECKLIST.md',
    'docs/setup/INSTALLATION.md',
    'docs/setup/LOCAL_ONLY_GUIDE.md',
    'docs/setup/COMPATIBILITY.md',
    'docs/setup/VALIDATION.md',
    'examples/plugin-manifest.example.json',
    'assets/logo/orchestra.ico'
)

$adapters = @('codex','vscode','antigravity','claude-code','local-ai')

$templates = @(
    'generic-skill-template.md','review-output-template.md','audit-output-template.md',
    'routing-output-template.md','safety-gate-template.md','scorecard-template.md',
    'local-install-template.md'
)

$tests = @(
    'tests/behavior/BEHAVIOR_TEST_MATRIX.md',
    'tests/behavior/MANUAL_TESTING_GUIDE.md',
    'tests/behavior/GOVERNANCE_SCENARIOS.md'
)

$missing = [System.Collections.Generic.List[string]]::new()

# Load manifest as single source of truth
$manifest = Get-JsonManifest (Join-Path $Root 'plugin.json')
$manifestSkills = $manifest.skills
$manifestCommands = $manifest.commands

Write-ColorHost 'INFO' 'Structure Validator: Verifying root repository files...'
foreach ($file in $requiredRoot) {
    if (-not (Test-FileNotEmpty (Join-Path $Root $file))) {
        $missing.Add($file)
    }
}

Write-ColorHost 'INFO' 'Structure Validator: Verifying manifest-declared skills and assets...'
foreach ($skill in $manifestSkills) {
    # Verify SKILL.md exists
    $skillMd = Join-Path $Root $skill.skill_path
    if (-not (Test-FileNotEmpty $skillMd)) {
        $missing.Add($skill.skill_path)
    }

    # Verify OUTPUT_FORMATS.md exists in same directory
    $skillFolder = Split-Path $skillMd -Parent
    $formatsFile = Join-Path $skillFolder 'OUTPUT_FORMATS.md'
    $formatsFileRelative = $formatsFile.Substring($Root.Length + 1)
    if (-not (Test-FileNotEmpty $formatsFile)) {
        $missing.Add($formatsFileRelative)
    }

    # Verify icon_path exists
    $iconPath = Join-Path $Root $skill.icon_path
    if (-not (Test-FileNotEmpty $iconPath)) {
        $missing.Add($skill.icon_path)
    }
}

Write-ColorHost 'INFO' 'Structure Validator: Verifying manifest-declared commands...'
foreach ($command in $manifestCommands) {
    $commandFile = "commands/$command.md"
    if (-not (Test-FileNotEmpty (Join-Path $Root $commandFile))) {
        $missing.Add($commandFile)
    }
}

Write-ColorHost 'INFO' 'Structure Validator: Verifying adapters, templates and test configurations...'
foreach ($adapter in $adapters) {
    $path = Join-Path $Root "adapters/$adapter"
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        $missing.Add("adapters/$adapter")
    }
}

foreach ($template in $templates) {
    $path = Join-Path $Root "templates/$template"
    if (-not (Test-FileNotEmpty $path)) {
        $missing.Add("templates/$template")
    }
}

foreach ($test_file in $tests) {
    $path = Join-Path $Root $test_file
    if (-not (Test-FileNotEmpty $path)) {
        $missing.Add($test_file)
    }
}

if ($missing.Count -gt 0) {
    foreach ($m in $missing) {
        Write-ColorHost 'ERROR' "Missing or invalid file: $m"
    }
    exit 1
}

Write-ColorHost 'SUCCESS' "Structure valid: $($manifestSkills.Count) skills, $($manifestCommands.Count) commands, $($adapters.Count) adapters, $($templates.Count) templates, $($tests.Count) tests verified."
exit 0

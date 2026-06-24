param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$requiredRoot = @(
    'README.md',
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
    'assets/logo/orchestra-of-amalgamation.ico'
)

$skills = @(
    'amalgam-conductor','cloak-meister','scribe-meister','meister-weaver',
    'meister-chronicler','acme-overseer','cipher-meister','hidden-dagger',
    'clockwork-meister','the-steward','the-governor'
)

# Governance skills use camelCase icon filenames
$iconOverrides = @{
    'the-steward'  = 'theSteward'
    'the-governor' = 'theGovernor'
}

$commands = @(
    'amalgam-conductor','review-architecture','review-ui','review-db',
    'review-docs','diagram-check','qa-check','security-check',
    'resilience-check'
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

function Test-ValidFile($Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }

    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop
    }
    catch {
        return $false
    }

    if ($item.Length -lt 10) {
        return $false
    }

    return $true
}

$missing = [System.Collections.Generic.List[string]]::new()

foreach ($file in $requiredRoot) {
    if (-not (Test-ValidFile (Join-Path $Root $file))) {
        $missing.Add($file)
    }
}

foreach ($skill in $skills) {
    $path = Join-Path $Root "skills/$skill/SKILL.md"
    if (-not (Test-ValidFile $path)) {
        $missing.Add("skills/$skill/SKILL.md")
    }

    $formatPath = Join-Path $Root "skills/$skill/OUTPUT_FORMATS.md"
    if (-not (Test-ValidFile $formatPath)) {
        $missing.Add("skills/$skill/OUTPUT_FORMATS.md")
    }

    $iconName = if ($iconOverrides.ContainsKey($skill)) { $iconOverrides[$skill] } else { $skill }
    $icon = "assets/icons/$iconName.ico"
    if (-not (Test-ValidFile (Join-Path $Root $icon))) {
        $missing.Add($icon)
    }
}

foreach ($command in $commands) {
    $path = Join-Path $Root "commands/$command.md"
    if (-not (Test-ValidFile $path)) {
        $missing.Add("commands/$command.md")
    }
}

foreach ($adapter in $adapters) {
    $path = Join-Path $Root "adapters/$adapter"
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        $missing.Add("adapters/$adapter")
    }
}

foreach ($template in $templates) {
    $path = Join-Path $Root "templates/$template"
    if (-not (Test-ValidFile $path)) {
        $missing.Add("templates/$template")
    }
}

foreach ($test_file in $tests) {
    $path = Join-Path $Root $test_file
    if (-not (Test-ValidFile $path)) {
        $missing.Add($test_file)
    }
}

if ($missing.Count) {
    $missing | ForEach-Object { Write-Error "Missing or invalid: $_" }
    exit 1
}

Write-Output "Structure valid: $($skills.Count) skills, $($commands.Count) commands, $($adapters.Count) adapters, $($templates.Count) templates, $($tests.Count) tests."
Write-Output "Note: This script checks required file existence and rejects near-empty files. Run .\scripts\validate-manifest.ps1 to verify frontmatter-to-manifest consistency."

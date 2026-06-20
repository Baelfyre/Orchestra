param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$requiredRoot = @(
    'README.md','LICENSE','.gitignore','CONTRIBUTING.md','CHANGELOG.md',
    'SKILL_INDEX.md','FOUNDATION.md','INSTALLATION.md','LOCAL_ONLY_GUIDE.md',
    'COMPATIBILITY.md','VALIDATION.md','ROADMAP.md','ROUTING_MAP.md',
    'PLUGIN_READINESS.md','MANIFEST_SCHEMA.md','examples/plugin-manifest.example.json',
    'assets/logo/orchestra-of-amalgamation.png'
)
$skills = @(
    'amalgam-conductor','cloak-meister','scribe-meister','meister-weaver',
    'meister-chronicler','acme-overseer','cipher-meister','hidden-dagger'
)
$adapters = @('codex','vscode','antigravity','claude-code','local-ai')
$templates = @(
    'generic-skill-template.md','review-output-template.md','audit-output-template.md',
    'routing-output-template.md','safety-gate-template.md','scorecard-template.md',
    'local-install-template.md'
)
$tests = @(
    'tests/behavior/BEHAVIOR_TEST_MATRIX.md',
    'tests/behavior/MANUAL_TESTING_GUIDE.md'
)

$missing = [System.Collections.Generic.List[string]]::new()
foreach ($file in $requiredRoot) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $file))) { $missing.Add($file) }
}
foreach ($skill in $skills) {
    $path = Join-Path $Root "skills/$skill/SKILL.md"
    if (-not (Test-Path -LiteralPath $path)) { $missing.Add("skills/$skill/SKILL.md") }

    $formatPath = Join-Path $Root "skills/$skill/OUTPUT_FORMATS.md"
    if (-not (Test-Path -LiteralPath $formatPath)) { $missing.Add("skills/$skill/OUTPUT_FORMATS.md") }

    $icon = "assets/icons/$skill.png"
    if (-not (Test-Path -LiteralPath (Join-Path $Root $icon))) { $missing.Add($icon) }
}
foreach ($adapter in $adapters) {
    $path = Join-Path $Root "adapters/$adapter"
    if (-not (Test-Path -LiteralPath $path)) { $missing.Add("adapters/$adapter") }
}
foreach ($template in $templates) {
    $path = Join-Path $Root "templates/$template"
    if (-not (Test-Path -LiteralPath $path)) { $missing.Add("templates/$template") }
}
foreach ($test_file in $tests) {
    $path = Join-Path $Root $test_file
    if (-not (Test-Path -LiteralPath $path)) { $missing.Add($test_file) }
}

if ($missing.Count) {
    $missing | ForEach-Object { Write-Error "Missing: $_" }
    exit 1
}

Write-Output "Structure valid: $($skills.Count) skills, $($adapters.Count) adapters, $($templates.Count) templates, $($tests.Count) tests."
Write-Output "Note: This script only checks file existence. Run .\scripts\validate-manifest.ps1 to verify frontmatter-to-manifest consistency."

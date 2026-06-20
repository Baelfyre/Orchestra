param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$requiredRoot = @(
    'README.md','LICENSE','.gitignore','CONTRIBUTING.md','CHANGELOG.md',
    'SKILL_INDEX.md','FOUNDATION.md','INSTALLATION.md','LOCAL_ONLY_GUIDE.md',
    'COMPATIBILITY.md','VALIDATION.md','ROADMAP.md',
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

$missing = [System.Collections.Generic.List[string]]::new()
foreach ($file in $requiredRoot) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $file))) { $missing.Add($file) }
}
foreach ($skill in $skills) {
    $path = Join-Path $Root "skills/$skill/SKILL.md"
    if (-not (Test-Path -LiteralPath $path)) { $missing.Add("skills/$skill/SKILL.md") }

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

if ($missing.Count) {
    $missing | ForEach-Object { Write-Error "Missing: $_" }
    exit 1
}

Write-Output "Structure valid: $($skills.Count) skills, $($adapters.Count) adapters, $($templates.Count) templates."

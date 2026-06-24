param(
    [string]$SourceRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$TargetRoot = $PSScriptRoot
)

$skills = @(
    'amalgam-conductor','cloak-meister','scribe-meister','meister-weaver',
    'meister-chronicler','acme-overseer','cipher-meister','hidden-dagger',
    'clockwork-meister'
)

$targetSkillsDir = Join-Path $TargetRoot "skills"
if (-not (Test-Path $targetSkillsDir)) {
    New-Item -ItemType Directory -Path $targetSkillsDir | Out-Null
}

foreach ($skill in $skills) {
    $sourceDir = Join-Path $SourceRoot "skills\$skill"
    $targetDir = Join-Path $targetSkillsDir $skill

    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir | Out-Null
    }

    # 1. Parse and rewrite SKILL.md
    $sourceSkillFile = Join-Path $sourceDir "SKILL.md"
    $targetSkillFile = Join-Path $targetDir "SKILL.md"
    
    $content = Get-Content $sourceSkillFile -Raw
    
    # Extract name and description using Regex
    $nameMatch = [regex]::Match($content, '(?m)^name:\s*(.+)$')
    $descMatch = [regex]::Match($content, '(?m)^description:\s*(.+)$')
    
    $name = if ($nameMatch.Success) { $nameMatch.Groups[1].Value } else { $skill }
    $desc = if ($descMatch.Success) { $descMatch.Groups[1].Value } else { "" }
    
    # Extract the body (everything after the second ---)
    $bodyMatch = [regex]::Match($content, '(?s)^---.*?---(.*)$')
    $body = if ($bodyMatch.Success) { $bodyMatch.Groups[1].Value } else { "" }

    # Ensure amalgam-conductor refers to local ROUTING_MAP.md instead of ../../
    if ($skill -eq 'amalgam-conductor') {
        $body = $body -replace '\.\./\.\./ROUTING_MAP\.md', './ROUTING_MAP.md'
    }

    $newFrontmatter = @"
---
name: $name
description: $desc
---
"@

    $newContent = $newFrontmatter + $body
    Set-Content -Path $targetSkillFile -Value $newContent -Encoding UTF8

    # 2. Copy OUTPUT_FORMATS.md
    $sourceOutFile = Join-Path $sourceDir "OUTPUT_FORMATS.md"
    $targetOutFile = Join-Path $targetDir "OUTPUT_FORMATS.md"
    if (Test-Path $sourceOutFile) {
        Copy-Item -Path $sourceOutFile -Destination $targetOutFile -Force
    }

    # 3. For amalgam-conductor, copy ROUTING_MAP.md
    if ($skill -eq 'amalgam-conductor') {
        $sourceRouting = Join-Path $SourceRoot "ROUTING_MAP.md"
        $targetRouting = Join-Path $targetDir "ROUTING_MAP.md"
        if (Test-Path $sourceRouting) {
            Copy-Item -Path $sourceRouting -Destination $targetRouting -Force
        }
    }
}

Write-Output "Codex skills exported successfully to $targetSkillsDir"

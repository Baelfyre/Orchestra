param(
    [string]$SourceRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$TargetRoot = $PSScriptRoot
)

$manifestPath = Join-Path $SourceRoot "plugin.json"
if (-not (Test-Path $manifestPath)) {
    Write-Error "plugin.json not found at $manifestPath"
    exit 1
}
$manifest = Get-Content -Raw -Path $manifestPath | ConvertFrom-Json
$skills = $manifest.skills | Where-Object { $_.activation_level -ne 'Governor' } | Select-Object -ExpandProperty slug

function Write-Utf8NoBomLfFile {
    param(
        [string]$Path,
        [string]$Content
    )

    $normalized = $Content -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($Path, $normalized, [System.Text.UTF8Encoding]::new($false))
}

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

    # Ensure conductor refers to local ROUTING_MAP.md instead of ../../
    if ($skill -eq 'conductor') {
        $body = $body -replace '\.\./\.\./ROUTING_MAP\.md', './ROUTING_MAP.md'
    }

    $newFrontmatter = @"
---
name: $name
description: $desc
---
"@

    $newContent = $newFrontmatter + $body
    Write-Utf8NoBomLfFile -Path $targetSkillFile -Content $newContent

    # 2. Copy OUTPUT_FORMATS.md
    $sourceOutFile = Join-Path $sourceDir "OUTPUT_FORMATS.md"
    $targetOutFile = Join-Path $targetDir "OUTPUT_FORMATS.md"
    if (Test-Path $sourceOutFile) {
        $outContent = Get-Content -Raw -Path $sourceOutFile
        Write-Utf8NoBomLfFile -Path $targetOutFile -Content $outContent
    }

    # 3. For conductor, copy ROUTING_MAP.md
    if ($skill -eq 'conductor') {
        $sourceRouting = Join-Path $SourceRoot "ROUTING_MAP.md"
        $targetRouting = Join-Path $targetDir "ROUTING_MAP.md"
        if (Test-Path $sourceRouting) {
            $routingContent = Get-Content -Raw -Path $sourceRouting
            Write-Utf8NoBomLfFile -Path $targetRouting -Content $routingContent
        }
    }
}

Write-Output "Codex skills exported successfully to $targetSkillsDir"

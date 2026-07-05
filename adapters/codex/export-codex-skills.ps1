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
$skills = $manifest.skills | Select-Object -ExpandProperty slug

function Write-Utf8NoBomLfFile {
    param(
        [string]$Path,
        [string]$Content
    )

    $normalized = $Content -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($Path, $normalized, [System.Text.UTF8Encoding]::new($false))
}

function Read-Utf8TextFile {
    param(
        [string]$Path
    )

    return [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($false))
}

function Copy-RelativeMarkdownFile {
    param(
        [string]$SourceRoot,
        [string]$TargetRoot,
        [string]$RelativePath
    )

    $sourceFile = Join-Path $SourceRoot $RelativePath
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        return
    }

    $targetFile = Join-Path $TargetRoot $RelativePath
    $targetFileDir = Split-Path -Parent $targetFile

    if (-not (Test-Path -LiteralPath $targetFileDir -PathType Container)) {
        New-Item -ItemType Directory -Path $targetFileDir | Out-Null
    }

    $content = Read-Utf8TextFile -Path $sourceFile
    Write-Utf8NoBomLfFile -Path $targetFile -Content $content
}

$targetSkillsDir = Join-Path $TargetRoot "skills"
if (-not (Test-Path $targetSkillsDir)) {
    New-Item -ItemType Directory -Path $targetSkillsDir | Out-Null
}

foreach ($skill in $skills) {
    $sourceDir = Join-Path $SourceRoot "skills\$skill"
    $targetDir = Join-Path $targetSkillsDir $skill

    if (-not (Test-Path -LiteralPath $sourceDir -PathType Container)) {
        Write-Error "Source skill directory not found: $sourceDir"
        exit 1
    }

    if (Test-Path -LiteralPath $targetDir) {
        Remove-Item -LiteralPath $targetDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $targetDir | Out-Null

    # 1. Parse and rewrite SKILL.md
    $sourceSkillFile = Join-Path $sourceDir "SKILL.md"
    $targetSkillFile = Join-Path $targetDir "SKILL.md"
    
    $content = Read-Utf8TextFile -Path $sourceSkillFile
    
    # Extract name and description using Regex
    $nameMatch = [regex]::Match($content, '(?m)^name:\s*(.+)$')
    $descMatch = [regex]::Match($content, '(?m)^description:\s*(.+)$')
    
    $name = if ($nameMatch.Success) { $nameMatch.Groups[1].Value } else { $skill }
    $desc = if ($descMatch.Success) { $descMatch.Groups[1].Value } else { "" }
    
    # Extract the body (everything after the second ---)
    $bodyMatch = [regex]::Match($content, '(?s)^---.*?---(.*)$')
    $body = if ($bodyMatch.Success) { $bodyMatch.Groups[1].Value } else { "" }

    # Package-level Conductor runs without the repo root beside the skill.
    if ($skill -eq 'conductor') {
        $body = $body -replace '\.\./\.\./docs/', 'docs/'
        $body = $body -replace '\.\./\.\./SKILL_INDEX\.md', 'SKILL_INDEX.md'
        $body = $body -replace '\.\./\.\./ROUTING_MAP\.md', 'ROUTING_MAP.md'
    }

    $newFrontmatter = @"
---
name: $name
description: $desc
---
"@

    $newContent = $newFrontmatter + $body
    Write-Utf8NoBomLfFile -Path $targetSkillFile -Content $newContent

    # 2. Copy Markdown support files referenced by progressive disclosure links.
    $supportFiles = Get-ChildItem -Path $sourceDir -Recurse -File -Filter "*.md" | Where-Object { $_.Name -ne "SKILL.md" }
    foreach ($supportFile in $supportFiles) {
        $relativePath = $supportFile.FullName.Substring($sourceDir.Length).TrimStart('\', '/')
        $targetSupportFile = Join-Path $targetDir $relativePath
        $targetSupportDir = Split-Path -Parent $targetSupportFile

        if (-not (Test-Path -LiteralPath $targetSupportDir -PathType Container)) {
            New-Item -ItemType Directory -Path $targetSupportDir | Out-Null
        }

        $supportContent = Read-Utf8TextFile -Path $supportFile.FullName
        Write-Utf8NoBomLfFile -Path $targetSupportFile -Content $supportContent
    }

    # 3. For conductor, copy root router docs needed by progressive disclosure.
    if ($skill -eq 'conductor') {
        foreach ($rootDoc in @("ROUTING_MAP.md", "SKILL_INDEX.md")) {
            $sourceDoc = Join-Path $SourceRoot $rootDoc
            $targetDoc = Join-Path $targetDir $rootDoc
            if (Test-Path -LiteralPath $sourceDoc -PathType Leaf) {
                $docContent = Read-Utf8TextFile -Path $sourceDoc
                Write-Utf8NoBomLfFile -Path $targetDoc -Content $docContent
            }
        }

        foreach ($supportDoc in @(
            "docs\routing\EXECUTION_MODES_POLICY.md",
            "docs\routing\CONTEXT_RETRIEVAL_RULES.md",
            "docs\routing\MINIMAL_PROMPT_FORMAT.md",
            "docs\governance\GOVERNANCE_LAYER.md"
        )) {
            Copy-RelativeMarkdownFile -SourceRoot $SourceRoot -TargetRoot $targetDir -RelativePath $supportDoc
        }
    }
}

Write-Output "Codex skills exported successfully to $targetSkillsDir"

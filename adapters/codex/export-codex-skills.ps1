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

$portableReferences = @{
    "conductor" = @(
        [pscustomobject]@{ Source = "docs/routing/EXECUTION_MODES_POLICY.md"; Canonical = "../../docs/routing/EXECUTION_MODES_POLICY.md"; Export = "REFERENCE_CONTEXT.md#execution-modes-policy"; Anchor = "execution-modes-policy" },
        [pscustomobject]@{ Source = "SKILL_INDEX.md"; Canonical = "../../SKILL_INDEX.md"; Export = "REFERENCE_CONTEXT.md#skill-index"; Anchor = "skill-index" },
        [pscustomobject]@{ Source = "docs/routing/MINIMAL_PROMPT_FORMAT.md"; Canonical = "../../docs/routing/MINIMAL_PROMPT_FORMAT.md"; Export = "REFERENCE_CONTEXT.md#minimal-prompt-format"; Anchor = "minimal-prompt-format" },
        [pscustomobject]@{ Source = "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"; Canonical = "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"; Export = "REFERENCE_CONTEXT.md#governance-decision-protocol"; Anchor = "governance-decision-protocol" }
    )
    "the-steward" = @(
        [pscustomobject]@{ Source = "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"; Canonical = "../../docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"; Export = "REFERENCE_CONTEXT.md#governance-decision-protocol"; Anchor = "governance-decision-protocol" },
        [pscustomobject]@{ Source = "docs/governance/PROJECT_CONTEXT_DECISION_PROMPT.md"; Canonical = "../../docs/governance/PROJECT_CONTEXT_DECISION_PROMPT.md"; Export = "REFERENCE_CONTEXT.md#project-context-decision-prompt"; Anchor = "project-context-decision-prompt" },
        [pscustomobject]@{ Source = "docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md"; Canonical = "../../docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md"; Export = "REFERENCE_CONTEXT.md#project-context-enforcement-policy"; Anchor = "project-context-enforcement-policy" },
        [pscustomobject]@{ Source = "docs/templates/PROJECT_CONTEXT_TEMPLATE.md"; Canonical = "../../docs/templates/PROJECT_CONTEXT_TEMPLATE.md"; Export = "REFERENCE_CONTEXT.md#project-context-template"; Anchor = "project-context-template" }
    )
    "the-governor" = @(
        [pscustomobject]@{ Source = "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"; Canonical = "../../docs/governance/GOVERNANCE_DECISION_PROTOCOL.md"; Export = "REFERENCE_CONTEXT.md#governance-decision-protocol"; Anchor = "governance-decision-protocol" }
    )
}

function Write-PortableReferenceContext {
    param(
        [string]$Skill,
        [string]$TargetDir
    )

    $references = $portableReferences[$Skill]
    if (-not $references) {
        return
    }

    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add("# Portable Reference Context")
    $lines.Add("")
    $lines.Add("Generated from canonical Orchestra sources. Indented snapshots are code-only context; file references inside snapshots are not package navigation targets.")

    foreach ($reference in $references) {
        $sourcePath = Join-Path $SourceRoot $reference.Source
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            Write-Error "Portable reference source not found: $sourcePath"
            exit 1
        }

        $lines.Add("")
        $lines.Add("<a id=`"$($reference.Anchor)`"></a>")
        $lines.Add("## Source: $($reference.Source)")
        $lines.Add("")
        $sourceText = (Read-Utf8TextFile -Path $sourcePath) -replace "`r`n", "`n"
        foreach ($sourceLine in $sourceText.TrimEnd([char[]]"`r`n") -split "`n") {
            $cleanSourceLine = $sourceLine.TrimEnd()
            if ($cleanSourceLine) {
                $lines.Add("    $cleanSourceLine")
            }
            else {
                $lines.Add("")
            }
        }
    }

    $bundlePath = Join-Path $TargetDir "REFERENCE_CONTEXT.md"
    Write-Utf8NoBomLfFile -Path $bundlePath -Content (($lines -join "`n") + "`n")
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

    # Package external references inside each exported skill.
    foreach ($reference in $portableReferences[$skill]) {
        $body = $body.Replace($reference.Canonical, $reference.Export)
    }

    # Conductor keeps its routing map as a first-class package-local file.
    if ($skill -eq 'conductor') {
        $body = $body.Replace('../../ROUTING_MAP.md', 'ROUTING_MAP.md')
    }

    $newFrontmatter = @"
---
name: $name
description: $desc
---
"@

    $newContent = $newFrontmatter + $body
    Write-Utf8NoBomLfFile -Path $targetSkillFile -Content $newContent

    Write-PortableReferenceContext -Skill $skill -TargetDir $targetDir

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

    # 3. For conductor, copy ROUTING_MAP.md
    if ($skill -eq 'conductor') {
        $sourceRouting = Join-Path $SourceRoot "ROUTING_MAP.md"
        $targetRouting = Join-Path $targetDir "ROUTING_MAP.md"
        if (Test-Path $sourceRouting) {
            $routingContent = Read-Utf8TextFile -Path $sourceRouting
            foreach ($reference in $portableReferences['conductor']) {
                $routingContent = $routingContent.Replace($reference.Canonical, $reference.Export)
            }
            Write-Utf8NoBomLfFile -Path $targetRouting -Content $routingContent
        }
    }
}

Write-Output "Codex skills exported successfully to $targetSkillsDir"

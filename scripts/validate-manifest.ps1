# Re-architected Manifest Validator Script
# Uses shared helper functions and checks frontmatter alignment.

param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$ManifestPath = ".\plugin.json"
)

$ErrorActionPreference = 'Stop'

# Import shared helpers
$helpersPath = Join-Path $PSScriptRoot 'helpers.ps1'
if (-not (Test-Path $helpersPath)) {
    Write-Error "Helpers module missing at: $helpersPath"
    exit 1
}
. $helpersPath

if (-not [System.IO.Path]::IsPathRooted($ManifestPath)) {
    $ManifestPath = Join-Path $Root $ManifestPath
}

# 1. Load Manifest & Skills
$manifest = Get-JsonManifest $ManifestPath
$manifestSkills = $manifest.skills

$skillsDir = Join-Path $Root "skills"
$skillFolders = Get-ChildItem -LiteralPath $skillsDir -Directory

$skillIndexLines = Get-Content -LiteralPath (Join-Path $Root "SKILL_INDEX.md")

$errors = 0

Write-ColorHost 'INFO' 'Manifest Validator: Cross-checking folders with manifest entries...'

# Check that every manifest skill has a real folder
foreach ($ms in $manifestSkills) {
    $folderPath = Join-Path $skillsDir $ms.slug
    if (-not (Test-Path -LiteralPath $folderPath)) {
        Write-ColorHost 'ERROR' "Manifest lists skill '$($ms.slug)' but folder does not exist."
        $errors++
    }
}

# Iterate through actual folders and compare to manifest
foreach ($folder in $skillFolders) {
    $skillName = $folder.Name
    $skillMdPath = Join-Path $folder.FullName "SKILL.md"
    
    if (-not (Test-Path -LiteralPath $skillMdPath)) {
        continue # handled by structure validation
    }

    $ms = $manifestSkills | Where-Object { $_.slug -eq $skillName }
    if (-not $ms) {
        Write-ColorHost 'ERROR' "Skill folder '$skillName' exists but is not listed in the manifest."
        $errors++
        continue
    }

    # Verify paths in manifest exist
    $expectedSkillPath = Join-Path $Root $ms.skill_path
    if (-not (Test-Path -LiteralPath $expectedSkillPath)) {
        Write-ColorHost 'ERROR' "Manifest skill_path '$($ms.skill_path)' for '$skillName' does not exist."
        $errors++
    }
    
    $expectedIconPath = Join-Path $Root $ms.icon_path
    if (-not (Test-Path -LiteralPath $expectedIconPath)) {
        Write-ColorHost 'ERROR' "Manifest icon_path '$($ms.icon_path)' for '$skillName' does not exist."
        $errors++
    }

    # Parse YAML frontmatter
    try {
        $frontmatter = Parse-Frontmatter $skillMdPath
        $fields = @("name","description","slug","role","primary_use","avoid_when","activation_level","depends_on","output_formats")
        
        $skillOutputFormats = @()
        foreach ($field in $fields) {
            $val = $frontmatter[$field]
            $manifestVal = $ms.$field

            if ($null -eq $val) {
                Write-ColorHost 'ERROR' "Missing field '$field' in frontmatter of $skillName"
                $errors++
                continue
            }

            if ($field -eq "output_formats") {
                # Handle array comparison (e.g. "[Compact, Full]")
                $val = $val -replace '\[|\]',''
                $arr = $val -split ',' | ForEach-Object { $_.Trim() }
                $skillOutputFormats = $arr
                $mArr = $manifestVal
                
                $valStr = ($arr -join ',')
                $mValStr = ($mArr -join ',')
                
                if ($valStr -ne $mValStr) {
                    Write-ColorHost 'ERROR' "Mismatch in $skillName -> output_formats. Frontmatter: '$valStr', Manifest: '$mValStr'"
                    $errors++
                }
            } else {
                if ($val -ne $manifestVal) {
                    Write-ColorHost 'ERROR' "Mismatch in $skillName -> $field. Frontmatter: '$val', Manifest: '$manifestVal'"
                    $errors++
                }
            }
        }
        
        # Check OUTPUT_FORMATS.md headings
        $formatsPath = Join-Path $folder.FullName "OUTPUT_FORMATS.md"
        if (Test-Path -LiteralPath $formatsPath) {
            $formatsContent = Get-Content -LiteralPath $formatsPath -Raw
            foreach ($format in $skillOutputFormats) {
                $escapedFormat = [regex]::Escape($format)
                if ($formatsContent -notmatch "(?m)^##\s+${escapedFormat}(?:\s*$|\s*[:\(].*$)") {
                    Write-ColorHost 'ERROR' "Output format drift: Heading '## $format' missing in OUTPUT_FORMATS.md for $skillName"
                    $errors++
                }
            }
        }

        # Check SKILL_INDEX.md row sync
        $escapedSlug = [regex]::Escape($skillName)
        $indexRow = $skillIndexLines | Where-Object { $_ -match ('\|\s*`' + $escapedSlug + '`\s*\|') } | Select-Object -First 1
        if ($indexRow) {
            $columns = $indexRow -split '\|'
            if ($columns.Count -ge 9) {
                $indexFormatsRaw = $columns[-2]
                $indexFormatsRaw = $indexFormatsRaw -replace '`',''
                $indexArr = $indexFormatsRaw -split ',' | ForEach-Object { $_.Trim() }
                $indexValStr = ($indexArr -join ',')
                $valStr = ($skillOutputFormats -join ',')

                if ($indexValStr -ne $valStr) {
                    Write-ColorHost 'ERROR' "SKILL_INDEX.md drift: Output formats for $skillName do not match frontmatter. Expected: '$valStr', Found: '$indexValStr'"
                    $errors++
                }
            } else {
                Write-ColorHost 'ERROR' "Invalid column count in SKILL_INDEX.md for $skillName"
                $errors++
            }
        } else {
            Write-ColorHost 'ERROR' "Could not find row for $skillName in SKILL_INDEX.md"
            $errors++
        }
    }
    catch {
        Write-ColorHost 'ERROR' "Could not parse frontmatter in $skillMdPath"
        $errors++
    }
}

if ($errors -gt 0) {
    Write-ColorHost 'ERROR' "Manifest validation failed with $errors errors."
    exit 1
}

Write-ColorHost 'SUCCESS' "Manifest validation successful. All skills perfectly match the frontmatter source of truth."
exit 0

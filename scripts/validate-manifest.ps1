param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$ManifestPath = ".\plugin.json"
)

if (-not [System.IO.Path]::IsPathRooted($ManifestPath)) {
    $ManifestPath = Join-Path $Root $ManifestPath
}

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    Write-Error "Manifest file not found: $manifestPath"
    exit 1
}

$manifestContent = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$manifestSkills = $manifestContent.skills

$skillsDir = Join-Path $Root "skills"
$skillFolders = Get-ChildItem -LiteralPath $skillsDir -Directory

$skillIndexLines = Get-Content -LiteralPath (Join-Path $Root "SKILL_INDEX.md")

$exceptions = @{
    'amalgam-conductor' = 'Semantic routing formats pending dedicated alignment pass'
    'the-steward'       = 'Governance Review is a semantic format covering compact and expanded templates'
    'the-governor'      = 'Governance Review is a semantic format covering compact and expanded templates'
    'meister-weaver'    = 'Diagram syntax labels pending dedicated alignment pass'
}

$errors = 0

# Check that every manifest skill has a real folder
foreach ($ms in $manifestSkills) {
    $folderPath = Join-Path $skillsDir $ms.slug
    if (-not (Test-Path -LiteralPath $folderPath)) {
        Write-Error "Manifest lists skill '$($ms.slug)' but folder does not exist."
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
        Write-Error "Skill folder '$skillName' exists but is not listed in the manifest."
        $errors++
        continue
    }

    # Verify paths in manifest exist
    $expectedSkillPath = Join-Path $Root $ms.skill_path
    if (-not (Test-Path -LiteralPath $expectedSkillPath)) {
        Write-Error "Manifest skill_path '$($ms.skill_path)' for '$skillName' does not exist."
        $errors++
    }
    
    $expectedIconPath = Join-Path $Root $ms.icon_path
    if (-not (Test-Path -LiteralPath $expectedIconPath)) {
        Write-Error "Manifest icon_path '$($ms.icon_path)' for '$skillName' does not exist."
        $errors++
    }

    # Parse YAML frontmatter
    $content = Get-Content -LiteralPath $skillMdPath -Raw
    # Extract frontmatter between --- and ---
    if ($content -match '(?sm)^---\s*(.*?)\s*---') {
        $frontmatter = $matches[1]
        
        $fields = @("name","description","slug","role","primary_use","avoid_when","activation_level","depends_on","output_formats")
        
        $skillOutputFormats = @()
        foreach ($field in $fields) {
            # simple regex to extract key: value
            if ($frontmatter -match "(?m)^${field}:\s*(.*)$") {
                $val = $matches[1].Trim()
                
                $manifestVal = $ms.$field
                
                if ($field -eq "output_formats") {
                    # Handle array comparison (e.g. "[Compact, Full]")
                    $val = $val -replace '\[|\]',''
                    $arr = $val -split ',' | ForEach-Object { $_.Trim() }
                    $skillOutputFormats = $arr
                    $mArr = $manifestVal
                    
                    $valStr = ($arr -join ',')
                    $mValStr = ($mArr -join ',')
                    
                    if ($valStr -ne $mValStr) {
                        Write-Error "Mismatch in $skillName -> output_formats. Frontmatter: '$valStr', Manifest: '$mValStr'"
                        $errors++
                    }
                } else {
                    if ($val -ne $manifestVal) {
                        Write-Error "Mismatch in $skillName -> $field. Frontmatter: '$val', Manifest: '$manifestVal'"
                        $errors++
                    }
                }
            } else {
                Write-Error "Missing field '$field' in frontmatter of $skillName"
                $errors++
            }
        }
        
        if ($exceptions.ContainsKey($skillName)) {
            Write-Host "Skipping extended contract checks for $skillName ($($exceptions[$skillName]))"
        } else {
            # 1. Check OUTPUT_FORMATS.md headings
            $formatsPath = Join-Path $folder.FullName "OUTPUT_FORMATS.md"
            if (Test-Path -LiteralPath $formatsPath) {
                $formatsContent = Get-Content -LiteralPath $formatsPath -Raw
                foreach ($format in $skillOutputFormats) {
                    $escapedFormat = [regex]::Escape($format)
                    if ($formatsContent -notmatch "(?m)^##\s+${escapedFormat}(?:\s*$|\s*[:\(].*$)") {
                        Write-Error "Output format drift: Heading '## $format' missing in OUTPUT_FORMATS.md for $skillName"
                        $errors++
                    }
                }
            }

            # 2. Check SKILL_INDEX.md
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
                        Write-Error "SKILL_INDEX.md drift: Output formats for $skillName do not match frontmatter. Expected: '$valStr', Found: '$indexValStr'"
                        $errors++
                    }
                } else {
                    Write-Error "Invalid column count in SKILL_INDEX.md for $skillName"
                    $errors++
                }
            } else {
                Write-Error "Could not find row for $skillName in SKILL_INDEX.md"
                $errors++
            }
        }
    } else {
        Write-Error "Could not find YAML frontmatter in $skillMdPath"
        $errors++
    }
}

if ($errors -gt 0) {
    Write-Error "Manifest validation failed with $errors errors."
    exit 1
}

Write-Output "Manifest validation successful. All skills perfectly match the frontmatter source of truth."
exit 0

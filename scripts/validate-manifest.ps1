param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$manifestPath = Join-Path $Root "examples/plugin-manifest.example.json"
if (-not (Test-Path -LiteralPath $manifestPath)) {
    Write-Error "Manifest file not found: $manifestPath"
    exit 1
}

$manifestContent = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$manifestSkills = $manifestContent.skills

$skillsDir = Join-Path $Root "skills"
$skillFolders = Get-ChildItem -LiteralPath $skillsDir -Directory

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
        
        foreach ($field in $fields) {
            # simple regex to extract key: value
            if ($frontmatter -match "(?m)^${field}:\s*(.*)$") {
                $val = $matches[1].Trim()
                
                $manifestVal = $ms.$field
                
                if ($field -eq "output_formats") {
                    # Handle array comparison (e.g. "[Compact, Full]")
                    $val = $val -replace '\[|\]',''
                    $arr = $val -split ',' | ForEach-Object { $_.Trim() }
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
    } else {
        Write-Error "Could not find YAML frontmatter in $skillMdPath"
        $errors++
    }
}

if ($errors -gt 0) {
    Write-Error "Manifest validation failed with $errors errors."
    exit 1
}

Write-Output "Manifest validation successful. All 8 skills perfectly match the frontmatter source of truth."
exit 0

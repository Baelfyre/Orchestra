param()

$codexSkillsDir = Join-Path $PSScriptRoot "skills"
$SourceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$manifestPath = Join-Path $SourceRoot "plugin.json"
if (-not (Test-Path $manifestPath)) {
    Write-Error "plugin.json not found at $manifestPath"
    exit 1
}
$manifest = Get-Content -Raw -Path $manifestPath | ConvertFrom-Json
$skills = $manifest.skills | Where-Object { $_.activation_level -ne 'Governor' } | Select-Object -ExpandProperty slug

$errors = 0

foreach ($skill in $skills) {
    $skillDir = Join-Path $codexSkillsDir $skill
    if (-not (Test-Path $skillDir)) {
        Write-Error "Missing exported skill folder: $skillDir"
        $errors++
        continue
    }

    $skillFile = Join-Path $skillDir "SKILL.md"
    if (-not (Test-Path $skillFile)) {
        Write-Error "Missing SKILL.md in exported $skill"
        $errors++
    } else {
        $content = Get-Content $skillFile -Raw
        $fmMatch = [regex]::Match($content, '(?s)^---\r?\n(.*?)\r?\n---')
        if ($fmMatch.Success) {
            $fm = $fmMatch.Groups[1].Value
            $lines = $fm -split '\r?\n'
            foreach ($line in $lines) {
                if ($line -notmatch '^name:' -and $line -notmatch '^description:') {
                    Write-Error "Exported SKILL.md for $skill contains non-compliant frontmatter: $line"
                    $errors++
                }
            }
            if ($fm -notmatch "^name:\s*$skill") {
                Write-Error "Exported SKILL.md for $skill has mismatched name in frontmatter"
                $errors++
            }
        } else {
            Write-Error "Could not parse frontmatter in exported SKILL.md for $skill"
            $errors++
        }
    }

    $outFile = Join-Path $skillDir "OUTPUT_FORMATS.md"
    if (-not (Test-Path $outFile)) {
        Write-Error "Missing OUTPUT_FORMATS.md in exported $skill"
        $errors++
    }

    $staleRouting = Join-Path $skillDir "ROUTING_MATRIX.md"
    if (Test-Path $staleRouting) {
        Write-Error "Found stale ROUTING_MATRIX.md in exported $skill"
        $errors++
    }

    if ($skill -eq 'conductor') {
        $mapFile = Join-Path $skillDir "ROUTING_MAP.md"
        if (-not (Test-Path $mapFile)) {
            Write-Error "Missing ROUTING_MAP.md in exported conductor"
            $errors++
        }
    }
}

if ($errors -gt 0) {
    Write-Error "Codex export validation failed with $errors errors."
    exit 1
}

Write-Output "Codex export validation passed!"

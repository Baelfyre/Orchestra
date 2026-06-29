param(
    [Parameter(Mandatory=$true)]
    [string]$TargetRepo,
    
    [switch]$Force
)

$targetAgentsDir = Join-Path $TargetRepo ".agents\skills"
$sourceSkillsDir = Join-Path $PSScriptRoot "skills"

if (-not (Test-Path $sourceSkillsDir)) {
    Write-Error "Source skills directory not found: $sourceSkillsDir. Please run export-codex-skills.ps1 first."
    exit 1
}

if (-not (Test-Path $targetAgentsDir)) {
    New-Item -ItemType Directory -Path $targetAgentsDir -Force | Out-Null
}

$skills = Get-ChildItem -Path $sourceSkillsDir -Directory

foreach ($skill in $skills) {
    $dest = Join-Path $targetAgentsDir $skill.Name
    if (Test-Path -LiteralPath $dest) {
        if (-not $Force) {
            Write-Warning "Skill $($skill.Name) already exists at $dest. Skipping. Use -Force to overwrite."
            continue
        }

        # Replace the existing skill folder instead of nesting another copy inside it.
        Remove-Item -LiteralPath $dest -Recurse -Force
    }

    Copy-Item -LiteralPath $skill.FullName -Destination $dest -Recurse -Force
    Write-Output "Installed: $($skill.Name)"
}

Write-Output "Installation complete!"

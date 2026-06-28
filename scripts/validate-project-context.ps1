param (
    [string]$Mode = "Implementation Mode",
    [string]$ContextFile = "PROJECT_CONTEXT.md"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

$contextPath = Join-Path $Root $ContextFile

# If running against the framework repo itself, it might use PROJECT_STATE.md or just standard context.
# We will check if the file exists. If not, fallback to warning.
if (-not (Test-Path $contextPath)) {
    # If the project context is totally missing, and we're in Audit/Release mode, that's a failure.
    if ($Mode -match "Audit Mode|Release Mode") {
        Write-Host "[ERROR] The Steward: $ContextFile is missing. Cannot proceed with $Mode without context." -ForegroundColor Red
        exit 1
    } else {
        Write-Host "[WARNING] The Steward: $ContextFile is missing. This is allowed for $Mode but governance cannot be enforced." -ForegroundColor Yellow
        exit 0
    }
}

$content = Get-Content $contextPath -Raw

$requiredFields = @(
    "Project Type",
    "Goal",
    "Release Target",
    "Data Use",
    "Dependencies",
    "Constraints"
)

$missingFields = @()

foreach ($field in $requiredFields) {
    # Match something like "Project Type: value" or "**Project Type:** value"
    if (-not ($content -match "(?i)$field\s*:.*[^\s]")) {
        $missingFields += $field
    }
}

if ($missingFields.Count -gt 0) {
    $missingList = $missingFields -join ", "
    if ($Mode -match "Audit Mode|Release Mode") {
        Write-Host "[ERROR] The Steward: Project Context is incomplete. Missing required fields: $missingList" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "[WARNING] The Steward: Project Context is incomplete. Missing required fields: $missingList. Proceeding for $Mode." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "[SUCCESS] The Steward: Project Context is complete." -ForegroundColor Green
exit 0

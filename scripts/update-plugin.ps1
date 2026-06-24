param (
    [string]$RepoPath = ".",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "Amalgam Conductor: Safe Plugin Update Workflow" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Ensure RepoPath exists
if (-not (Test-Path -Path $RepoPath)) {
    Write-Host "[ERROR] The specified RepoPath does not exist: $RepoPath" -ForegroundColor Red
    exit 1
}

# Change directory to RepoPath
Push-Location -Path $RepoPath

try {
    # 1. Detect if inside a git repository
    $isGitRepo = $null
    try {
        $isGitRepo = git rev-parse --is-inside-work-tree 2>&1
    } catch {
        Write-Host "[ERROR] Not a git repository. The safe update script requires a git-cloned installation." -ForegroundColor Red
        exit 1
    }

    if ($isGitRepo -notmatch "true") {
        Write-Host "[ERROR] Not a git repository. The safe update script requires a git-cloned installation." -ForegroundColor Red
        exit 1
    }

    # 2. Detect the actual git repo root
    $repoRoot = git rev-parse --show-toplevel
    Write-Host "Repository root detected: $repoRoot"

    # 3. Stop if the working tree has uncommitted changes
    $status = git status --porcelain
    if ($status) {
        Write-Host "[ERROR] Working tree has uncommitted changes. Please commit or stash them before updating." -ForegroundColor Red
        Write-Host "Changes:"
        Write-Host $status
        exit 1
    }

    # 4. Detect current branch
    $currentBranch = git branch --show-current
    if ([string]::IsNullOrWhiteSpace($currentBranch)) {
        Write-Host "[ERROR] Could not detect the current branch. Are you in a detached HEAD state?" -ForegroundColor Red
        exit 1
    }
    Write-Host "Current branch: $currentBranch"

    if ($DryRun) {
        Write-Host "`n[DRY RUN] Would run: git fetch" -ForegroundColor Yellow
        Write-Host "[DRY RUN] Would run: git pull origin $currentBranch" -ForegroundColor Yellow
        Write-Host "[DRY RUN] Would run: .\scripts\validate-manifest.ps1" -ForegroundColor Yellow
        Write-Host "[DRY RUN] Would run: .\scripts\validate-structure.ps1" -ForegroundColor Yellow
        Write-Host "`nDry run complete. No changes made." -ForegroundColor Green
        exit 0
    }

    # 5. Run git fetch
    Write-Host "`nFetching latest changes from remote..." -ForegroundColor Cyan
    git fetch

    # 6. Pull the latest changes for the current branch
    Write-Host "Pulling latest changes for branch '$currentBranch'..." -ForegroundColor Cyan
    $pullResult = git pull origin $currentBranch 2>&1
    Write-Host $pullResult

    # 7. Run validations
    Write-Host "`nRunning validation scripts..." -ForegroundColor Cyan
    
    $manifestScript = Join-Path $repoRoot "scripts\validate-manifest.ps1"
    $structureScript = Join-Path $repoRoot "scripts\validate-structure.ps1"

    if (Test-Path $manifestScript) {
        Write-Host "Validating manifest..."
        powershell -ExecutionPolicy Bypass -File $manifestScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Manifest validation failed! Rollback recommended." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[WARNING] validate-manifest.ps1 not found." -ForegroundColor Yellow
    }

    if (Test-Path $structureScript) {
        Write-Host "Validating structure..."
        powershell -ExecutionPolicy Bypass -File $structureScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Structure validation failed! Rollback recommended." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[WARNING] validate-structure.ps1 not found." -ForegroundColor Yellow
    }

    # 8. Print success and reload instructions
    Write-Host "`n[SUCCESS] Update and validation completed successfully!" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "  - For Antigravity: Reload your plugins or restart the terminal session."
    Write-Host "  - For Codex: Restart the agent workspace to load the updated skills."

} finally {
    Pop-Location
}

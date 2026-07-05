# Shared Helper Functions for Orchestra Validation and Update Scripts

$ErrorActionPreference = 'Stop'

function Get-ProjectRoot {
    # Returns the absolute path of the repository root
    return (Split-Path -Parent $PSScriptRoot)
}

function Get-Aliases {
    $root = Get-ProjectRoot
    $aliasPath = Join-Path $root 'aliases.json'
    if (Test-Path -LiteralPath $aliasPath) {
        return Get-Content -LiteralPath $aliasPath -Raw | ConvertFrom-Json
    }
    return @{}
}

function Resolve-Slug {
    param([string]$Slug)
    $aliases = Get-Aliases
    if ($aliases.PSObject.Properties[$Slug]) {
        return $aliases.$Slug
    }
    return $Slug
}

function Test-FileNotEmpty {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop
        if ($item.Length -lt 10) {
            return $false
        }
    }
    catch {
        return $false
    }
    return $true
}

function Write-ColorHost {
    param(
        [ValidateSet('INFO', 'SUCCESS', 'WARNING', 'ERROR')]
        [string]$Type,
        [string]$Message
    )

    $color = switch ($Type) {
        'SUCCESS' { 'Green' }
        'WARNING' { 'Yellow' }
        'ERROR'   { 'Red' }
        default   { 'Cyan' }
    }

    Write-Host "[$Type] $Message" -ForegroundColor $color
}

function Get-JsonManifest {
    param([string]$Path = "")
    $root = Get-ProjectRoot
    if ([string]::IsNullOrEmpty($Path)) {
        $Path = Join-Path $root 'plugin.json'
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Manifest file not found at: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Parse-Frontmatter {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "File not found: $Path"
    }
    $content = Get-Content -LiteralPath $Path -Raw
    if ($content -match '(?sm)^---\s*(.*?)\s*---') {
        $frontmatterText = $matches[1]
        $fields = [ordered]@{}
        
        # Parse simple key-value YAML fields
        $lines = $frontmatterText -split "\r?\n"
        foreach ($line in $lines) {
            if ($line -match "^([^:]+):\s*(.*)$") {
                $key = $matches[1].Trim()
                $val = $matches[2].Trim()
                $fields[$key] = $val
            }
        }
        return $fields
    }
    throw "Frontmatter not found in file: $Path"
}

function Test-WorkflowLocked {
    $root = Get-ProjectRoot
    $lockFile = Join-Path $root ".amalgam\lock.json"
    if (-not (Test-Path -LiteralPath $lockFile)) {
        return $false
    }
    try {
        $lock = Get-Content -LiteralPath $lockFile -Raw | ConvertFrom-Json
        $lockPid = $lock.pid
        $timestamp = [DateTime]$lock.timestamp

        $age = (Get-Date) - $timestamp
        if ($age.TotalHours -ge 1) { return $false }

        try {
            $p = Get-Process -Id $lockPid -ErrorAction SilentlyContinue
            if ($p) { return $true }
        }
        catch {}
    }
    catch {}
    return $false
}

function Get-DirectoryHashIndex {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Root
    )

    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        throw "Directory not found: $Root"
    }

    $rootItem = Get-Item -LiteralPath $Root -ErrorAction Stop
    $normalizedRoot = $rootItem.FullName.TrimEnd('\', '/')
    $index = @{}

    Get-ChildItem -LiteralPath $normalizedRoot -Recurse -File | ForEach-Object {
        $relativePath = $_.FullName.Substring($normalizedRoot.Length).TrimStart('\', '/').Replace('\', '/')
        $index[$relativePath] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }

    return $index
}

function Compare-DirectoryParity {
    param(
        [Parameter(Mandatory=$true)]
        [string]$SourceRoot,

        [Parameter(Mandatory=$true)]
        [string]$DestinationRoot
    )

    $sourceIndex = Get-DirectoryHashIndex -Root $SourceRoot
    $destinationIndex = Get-DirectoryHashIndex -Root $DestinationRoot
    $issues = New-Object System.Collections.Generic.List[string]

    foreach ($relativePath in $sourceIndex.Keys) {
        if (-not $destinationIndex.ContainsKey($relativePath)) {
            $issues.Add("Missing file in destination: $relativePath")
            continue
        }

        if ($sourceIndex[$relativePath] -ne $destinationIndex[$relativePath]) {
            $issues.Add("Hash mismatch: $relativePath")
        }
    }

    foreach ($relativePath in $destinationIndex.Keys) {
        if (-not $sourceIndex.ContainsKey($relativePath)) {
            $issues.Add("Unexpected file in destination: $relativePath")
        }
    }

    return $issues
}

function Copy-SkillTree {
    param(
        [Parameter(Mandatory=$true)]
        [string]$SourceSkillsDir,

        [Parameter(Mandatory=$true)]
        [string]$DestinationSkillsDir
    )

    if (-not (Test-Path -LiteralPath $SourceSkillsDir -PathType Container)) {
        throw "Source skills directory not found: $SourceSkillsDir"
    }

    if (-not (Test-Path -LiteralPath $DestinationSkillsDir -PathType Container)) {
        New-Item -ItemType Directory -Path $DestinationSkillsDir -Force | Out-Null
    }

    $skills = Get-ChildItem -LiteralPath $SourceSkillsDir -Directory
    foreach ($skill in $skills) {
        $dest = Join-Path $DestinationSkillsDir $skill.Name
        if (Test-Path -LiteralPath $dest) {
            Remove-Item -LiteralPath $dest -Recurse -Force
        }

        Copy-Item -LiteralPath $skill.FullName -Destination $dest -Recurse -Force
        Write-Output "Installed: $($skill.Name)"
    }
}

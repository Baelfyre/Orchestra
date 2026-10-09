param(
    [ValidateSet('Acquire', 'Release', 'Check', 'LogDecision')]
    [string]$Action,

    [string]$SessionId,
    [string]$Details,
    [int]$ProcessId
)

$ErrorActionPreference = 'Stop'

# Source common helpers
$helpers = Join-Path $PSScriptRoot 'helpers.ps1'
if (Test-Path $helpers) {
    . $helpers
}

$root = Get-ProjectRoot
$lockFile = Join-Path $root ".amalgam\lock.json"

function Get-ActiveProcessPath {
    param([int]$TargetPid)
    try {
        $p = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
        if ($p) { return $p.Name }
    }
    catch {}
    return $null
}

function Check-Lock {
    if (-not (Test-Path -LiteralPath $lockFile)) {
        return $null
    }
    try {
        $lock = Get-Content -LiteralPath $lockFile -Raw | ConvertFrom-Json
        $lockPid = $lock.pid
        $timestamp = [DateTime]$lock.timestamp
        
        # Stale lock detection: 1 hour expiry
        $age = (Get-Date) - $timestamp
        if ($age.TotalHours -ge 1) {
            Write-ColorHost 'WARNING' "Stale lock detected (older than 1 hour)."
            return $null
        }

        # Check process active
        $pName = Get-ActiveProcessPath $lockPid
        if ($null -eq $pName) {
            Write-ColorHost 'WARNING' "Stale lock detected (process PID $lockPid is not running)."
            return $null
        }

        return $lock
    }
    catch {
        # Invalid JSON or corrupt lock file
        return $null
    }
}

function Acquire-Lock {
    $existing = Check-Lock
    if ($existing) {
        throw "LOCK_COLLISION: Active lock held by Session '$($existing.session_id)' (PID: $($existing.pid)) acquired at $($existing.timestamp)."
    }

    $lockData = [ordered]@{
        session_id = if ($SessionId) { $SessionId } else { [Guid]::NewGuid().ToString() }
        pid        = if ($ProcessId) { $ProcessId } else { $PID }
        timestamp  = (Get-Date).ToString('o')
    }

    # Ensure .amalgam folder exists
    $amalgamFolder = Split-Path -Parent $lockFile
    if (-not (Test-Path -LiteralPath $amalgamFolder)) {
        New-Item -ItemType Directory -Path $amalgamFolder | Out-Null
    }

    $lockDataJson = $lockData | ConvertTo-Json
    Set-Content -LiteralPath $lockFile -Value $lockDataJson -Encoding UTF8
    Write-ColorHost 'SUCCESS' "Lock acquired successfully for Session '$($lockData.session_id)'."
}

function Release-Lock {
    if (Test-Path -LiteralPath $lockFile) {
        Remove-Item -LiteralPath $lockFile -Force
        Write-ColorHost 'SUCCESS' "Lock released successfully."
    } else {
        Write-ColorHost 'INFO' "No active lock file found to release."
    }
}

function Log-Decision {
    if ([string]::IsNullOrWhiteSpace($Details)) {
        throw "LogDecision requires -Details."
    }
    $logPath = Join-Path $root "DECISION_LOG.md"
    $dateStr = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logEntry = "`n- [$dateStr] (PID: $PID) $Details"
    
    Add-Content -LiteralPath $logPath -Value $logEntry -Encoding UTF8
    Write-ColorHost 'SUCCESS' "Decision appended safely to DECISION_LOG.md"
}

switch ($Action) {
    'Check' {
        $active = Check-Lock
        if ($active) {
            Write-ColorHost 'WARNING' "Active lock held by Session '$($active.session_id)'."
            exit 1
        } else {
            Write-ColorHost 'SUCCESS' "No active lock."
            exit 0
        }
    }
    'Acquire' {
        try {
            Acquire-Lock
            exit 0
        }
        catch {
            Write-ColorHost 'ERROR' $_.Exception.Message
            exit 1
        }
    }
    'Release' {
        Release-Lock
        exit 0
    }
    'LogDecision' {
        try {
            Log-Decision
            exit 0
        }
        catch {
            Write-ColorHost 'ERROR' $_.Exception.Message
            exit 1
        }
    }
}

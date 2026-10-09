# Modularized Stale Reference Validator
# Scans files for deprecated, legacy, or private terms.

param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

# Import shared helpers
$helpersPath = Join-Path $PSScriptRoot 'helpers.ps1'
if (-not (Test-Path $helpersPath)) {
    Write-Error "Helpers module missing at: $helpersPath"
    exit 1
}
. $helpersPath

$patterns = @(
    'ux-diagram-' + 'architect',
    'meister-' + 'virtuoso',
    'Meister ' + 'Virtuoso',
    'AO' + 'OP',
    'Motor' + 'PH',
    'Hive' + 'Mind',
    'Art ' + 'Appreciation',
    ('C:' + '[\\/]' + 'Users' + '[\\/]'),
    ('/' + 'home' + '/'),
    '(?i)production\s+secrets?',
    '(?i)api[_ -]?keys?\s*[:=]\s*\S+'
)

$self = (Resolve-Path -LiteralPath $PSCommandPath).Path
$findings = Get-ChildItem -LiteralPath $Root -Recurse -File |
    Where-Object {
        $_.FullName -notmatch '[\\/]\.git[\\/]' -and
        $_.FullName -notmatch '[\\/]brain[\\/]' -and
        $_.FullName -ne $self
    } |
    Select-String -Pattern $patterns

if ($findings) {
    Write-ColorHost 'WARNING' 'Stale or disallowed references found:'
    $findings | ForEach-Object {
        Write-ColorHost 'ERROR' ("{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim())
    }
    exit 1
}

Write-ColorHost 'SUCCESS' 'No stale or disallowed references found.'
exit 0

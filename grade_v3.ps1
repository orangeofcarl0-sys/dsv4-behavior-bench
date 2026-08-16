# grade_v3.ps1 — host-side grading with the full v3 suites
# Usage: powershell -File grade_v3.ps1 -Repo <datapipe-repo-root> [-Label <name>] [-Python <path>] [-Heldout <path>]
param(
  [Parameter(Mandatory = $true)][string]$Repo,
  [string]$Label = '',
  [string]$Python = 'python',
  [string]$Heldout = ''
)
$ErrorActionPreference = 'Continue'
$v3 = Split-Path -Parent $MyInvocation.MyCommand.Path
$suites = @('d10','d11','d12','t2','t3','t4','v4')
$env:DATAPIPE_REPO = $Repo
$env:PYTHONPATH = $Repo
$results = @()
foreach ($s in $suites) {
  $out = & $Python -m pytest (Join-Path $v3 $s) -q --tb=no 2>&1 | Select-String 'passed|failed|no tests' | Select-Object -Last 1
  $results += $out.Line
}
$pub = & $Python -m pytest (Join-Path $Repo 'tests\public') -q --tb=no 2>&1 | Select-String 'passed|failed' | Select-Object -Last 1
$held = 'n/a'
if ($Heldout) { $held = (& $Python -m pytest $Heldout -q --tb=no 2>&1 | Select-String 'passed|failed' | Select-Object -Last 1).Line }
Remove-Item Env:\DATAPIPE_REPO -ErrorAction SilentlyContinue
Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue
$label = if ($Label) { $Label } else { Split-Path $Repo -Leaf }
Write-Output ("{0} | public: {1} | heldout: {2} | d10: {3} | d11: {4} | d12: {5} | t2: {6} | t3: {7} | t4: {8} | v4: {9}" -f $label, $pub.Line, $held, $results[0], $results[1], $results[2], $results[3], $results[4], $results[5], $results[6])

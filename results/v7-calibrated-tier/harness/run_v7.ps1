param(
  [Parameter(Mandatory=$true)][string]$Model,
  [int]$Rep = 1,
  [int]$HardCapMinutes = 60,
  [int]$GraceSeconds = 240
)
# run_v7.ps1 -- one agent run under the V7 task conditions.
$ErrorActionPreference = 'Continue'
$W    = '<harness>'
$Dsh  = '<appdata>\Roaming\npm\node_modules\@deepseek-ai\dsh\lib\bin.js'
$Node = 'C:\Program Files\nodejs\node.exe'
if (-not (Test-Path $Node)) { $Node = (Get-Command node.exe).Source }
$wd   = "$W\v7_runs\$Model\r$Rep"
$Log  = "$W\v7_logs\$Model"
New-Item -ItemType Directory -Force -Path $Log | Out-Null
if (-not (Test-Path $wd)) { Write-Host "MISSING workspace $wd"; exit 2 }

$task = (Get-Content "$W\TASK_PROMPT_v23.txt" -Raw) -replace "`r`n", "`n"
if ($task.Contains('"')) { throw 'task prompt contains a double quote' }

$nd  = "$Log\r$Rep.ndjson"
$argStr = '"' + $Dsh + '" --profile ef-dev --patch "' + "$W\og_model_$Model.yml" + '" headless --json "' + $task + '"'
$t0 = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
Set-Content -Path "$Log\r$Rep.start" -Value $t0 -NoNewline
$p = Start-Process -FilePath $Node -ArgumentList $argStr -WorkingDirectory $wd -PassThru -NoNewWindow `
     -RedirectStandardOutput $nd -RedirectStandardError "$Log\r$Rep.err"
$null = $p.Handle

$deadline = (Get-Date).AddMinutes($HardCapMinutes)
$rc = $null
while (-not $p.HasExited) {
    if ((Get-Date) -gt $deadline) { Write-Host "$Model r$Rep HARD CAP"; $p.Kill(); break }
    $hasFinal = $false
    if (Test-Path $nd) {
        try { if ((Get-Content $nd -Tail 40 -ErrorAction SilentlyContinue) -match '"type":"final"') { $hasFinal = $true } } catch { }
    }
    if ($hasFinal) {
        if (-not $p.WaitForExit($GraceSeconds * 1000)) {
            Write-Host "$Model r$Rep final seen, alive -> killing"
            $p.Kill(); $p.WaitForExit(30000); $rc = 'killed-after-final'; break
        }
        $rc = $p.ExitCode; break
    }
    Start-Sleep -Seconds 10
}
if ($null -eq $rc) { $rc = $p.ExitCode }
$t1 = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
Set-Content -Path "$Log\r$Rep.end" -Value $t1 -NoNewline
Set-Content -Path "$Log\r$Rep.rc"  -Value $rc  -NoNewline
Write-Host ("v7 {0} r{1} rc={2} wall={3}s ndjson={4}B" -f $Model, $Rep, $rc, ($t1 - $t0), (Get-Item $nd).Length)

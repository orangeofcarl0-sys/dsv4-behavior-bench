param([string[]]$Levels = @('low','medium','high','xhigh','max'))
# run_all_v5.ps1 -- N concurrent one-shot dsh headless runs on the V5 benchmark (datapipe v2.4).
# Runs under Windows PowerShell so dsh uses the Windows node and therefore the Windows
# DSH home (<user-home>\.dsh -> <dsh-home>) where profile 'ef-dev' lives.
$ErrorActionPreference = 'Continue'
$W    = '<harness>'
$Dsh  = '<appdata>\Roaming\npm\node_modules\@deepseek-ai\dsh\lib\bin.js'
$Node = 'C:\Program Files\nodejs\node.exe'
if (-not (Test-Path $Node)) { $Node = (Get-Command node.exe).Source }
$Log  = "$W\logs_v5"
New-Item -ItemType Directory -Force -Path $Log | Out-Null

$raw = Get-Content "$W\TASK_PROMPT.txt" -Raw
$task = $raw -replace "`r`n", "`n"
if ($task.Contains('"')) { throw 'task prompt contains a double quote; argv quoting would be unsafe' }
Write-Host ("task prompt: {0} chars, {1} lines" -f $task.Length, ($task -split "`n").Count)

$running = @()
foreach ($lv in $Levels) {
    $wd = "$W\runs_v5\$lv"
    if (-not (Test-Path $wd)) { Write-Host "MISSING workspace $wd"; continue }
    $argStr = '"' + $Dsh + '" --profile ef-dev --patch "' + "$W\effort_$lv.yml" + '" headless --json "' + $task + '"'
    $t0 = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    Set-Content -Path "$Log\$lv.start" -Value $t0 -NoNewline
    $p = Start-Process -FilePath $Node -ArgumentList $argStr -WorkingDirectory $wd -PassThru -NoNewWindow `
         -RedirectStandardOutput "$Log\$lv.ndjson" -RedirectStandardError "$Log\$lv.err"
    $null = $p.Handle   # cache the handle so ExitCode is readable after exit
    Write-Host ("launched {0} pid={1}" -f $lv, $p.Id)
    $running += [pscustomobject]@{ lv = $lv; proc = $p; t0 = $t0 }
}

foreach ($r in $running) {
    $r.proc.WaitForExit()
    $t1 = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $rc = $r.proc.ExitCode
    Set-Content -Path "$Log\$($r.lv).end" -Value $t1 -NoNewline
    Set-Content -Path "$Log\$($r.lv).rc"  -Value $rc   -NoNewline
    $size = (Get-Item "$Log\$($r.lv).ndjson").Length
    Write-Host ("{0} rc={1} wall={2}s ndjson={3}B" -f $r.lv, $rc, ($t1 - $r.t0), $size)
}
Write-Host 'ALL RUNS FINISHED'

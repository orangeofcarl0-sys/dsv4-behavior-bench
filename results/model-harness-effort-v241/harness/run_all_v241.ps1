param(
  [Parameter(Mandatory=$true)][int]$Rep,
  [string[]]$Levels = @('low','medium','high','xhigh','max'),
  [int]$HardCapMinutes = 150,
  [int]$GraceSeconds = 240
)
# run_all_v241.ps1 -Rep <n> -- one replicate of 5 concurrent space-bunny-free runs on V5 v2.4.1 (68 tests).
$ErrorActionPreference = 'Continue'
$W    = '<harness>'
$Dsh  = '<appdata>\Roaming\npm\node_modules\@deepseek-ai\dsh\lib\bin.js'
$Node = 'C:\Program Files\nodejs\node.exe'
if (-not (Test-Path $Node)) { $Node = (Get-Command node.exe).Source }
$Log  = "$W\logs_v241_r$Rep"
New-Item -ItemType Directory -Force -Path $Log | Out-Null

$raw = Get-Content "$W\TASK_PROMPT.txt" -Raw
$task = $raw -replace "`r`n", "`n"
if ($task.Contains('"')) { throw 'task prompt contains a double quote' }

$running = @()
foreach ($lv in $Levels) {
    $wd = "$W\runs_v241_r$Rep\$lv"
    if (-not (Test-Path $wd)) { Write-Host "MISSING $wd"; continue }
    $argStr = '"' + $Dsh + '" --profile ef-dev --patch "' + "$W\effort_$lv.yml" + '" headless --json "' + $task + '"'
    $t0 = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    Set-Content -Path "$Log\$lv.start" -Value $t0 -NoNewline
    $p = Start-Process -FilePath $Node -ArgumentList $argStr -WorkingDirectory $wd -PassThru -NoNewWindow `
         -RedirectStandardOutput "$Log\$lv.ndjson" -RedirectStandardError "$Log\$lv.err"
    $null = $p.Handle
    Write-Host ("v241 rep{0} launched {1} pid={2}" -f $Rep, $lv, $p.Id)
    $running += [pscustomobject]@{ lv = $lv; proc = $p; t0 = $t0; nd = "$Log\$lv.ndjson" }
}

$deadline = (Get-Date).AddMinutes($HardCapMinutes)
foreach ($r in $running) {
    $rc = $null
    while (-not $r.proc.HasExited) {
        if ((Get-Date) -gt $deadline) { Write-Host ("{0} HARD CAP" -f $r.lv); $r.proc.Kill(); break }
        $hasFinal = $false
        if (Test-Path $r.nd) {
            try {
                if ((Get-Content $r.nd -Tail 40 -ErrorAction SilentlyContinue) -match '"type":"final"') { $hasFinal = $true }
            } catch { }
        }
        if ($hasFinal) {
            if (-not $r.proc.WaitForExit($GraceSeconds * 1000)) {
                Write-Host ("{0} final seen, still alive after {1}s -> killing" -f $r.lv, $GraceSeconds)
                $r.proc.Kill(); $r.proc.WaitForExit(30000); $rc = 'killed-after-final'; break
            }
            $rc = $r.proc.ExitCode; break
        }
        Start-Sleep -Seconds 10
    }
    if ($null -eq $rc) { $rc = $r.proc.ExitCode }
    $t1 = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    Set-Content -Path "$Log\$($r.lv).end" -Value $t1 -NoNewline
    Set-Content -Path "$Log\$($r.lv).rc"  -Value $rc   -NoNewline
    Write-Host ("v241 rep{0} {1} rc={2} wall={3}s ndjson={4}B" -f $Rep, $r.lv, $rc, ($t1 - $r.t0), (Get-Item $r.nd).Length)
}
Write-Host "V241 REP $Rep FINISHED"

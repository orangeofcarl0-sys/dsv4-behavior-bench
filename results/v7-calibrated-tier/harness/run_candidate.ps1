param(
  [Parameter(Mandatory=$true)][string]$Model,
  [int]$Reps = 3,
  [int]$HardCapMinutes = 75,
  [int]$GraceSeconds = 240
)
# run_candidate.ps1 -- one candidate's replicates, run concurrently.
# The upstream account behind several OmniGate models caps concurrency at 3
# sessions, so replicates_per_candidate is the safe width; candidates run one
# at a time from the driver.
$ErrorActionPreference = 'Continue'
$W    = '<harness>'
$Dsh  = '<appdata>\Roaming\npm\node_modules\@deepseek-ai\dsh\lib\bin.js'
$Node = 'C:\Program Files\nodejs\node.exe'
if (-not (Test-Path $Node)) { $Node = (Get-Command node.exe).Source }
$Log  = "$W\legacy_logs\$Model"
New-Item -ItemType Directory -Force -Path $Log | Out-Null

$task = (Get-Content "$W\TASK_PROMPT_v23.txt" -Raw) -replace "`r`n", "`n"
if ($task.Contains('"')) { throw 'task prompt contains a double quote' }

$running = @()
foreach ($rep in 1..$Reps) {
    $wd = "$W\legacy_runs\$Model\r$rep"
    if (-not (Test-Path $wd)) { Write-Host "MISSING $wd"; continue }
    $nd = "$Log\r$rep.ndjson"
    $argStr = '"' + $Dsh + '" --profile ef-dev --patch "' + "$W\og_model_$Model.yml" + '" headless --json "' + $task + '"'
    $t0 = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    Set-Content -Path "$Log\r$rep.start" -Value $t0 -NoNewline
    $p = Start-Process -FilePath $Node -ArgumentList $argStr -WorkingDirectory $wd -PassThru -NoNewWindow `
         -RedirectStandardOutput $nd -RedirectStandardError "$Log\r$rep.err"
    $null = $p.Handle
    Write-Host ("launched {0} r{1} pid={2}" -f $Model, $rep, $p.Id)
    $running += [pscustomobject]@{ rep = $rep; proc = $p; t0 = $t0; nd = $nd }
}

$deadline = (Get-Date).AddMinutes($HardCapMinutes)
foreach ($r in $running) {
    $rc = $null
    while (-not $r.proc.HasExited) {
        if ((Get-Date) -gt $deadline) { Write-Host ("r{0} HARD CAP" -f $r.rep); $r.proc.Kill(); break }
        $hasFinal = $false
        if (Test-Path $r.nd) {
            try { if ((Get-Content $r.nd -Tail 40 -ErrorAction SilentlyContinue) -match '"type":"final"') { $hasFinal = $true } } catch { }
        }
        if ($hasFinal) {
            if (-not $r.proc.WaitForExit($GraceSeconds * 1000)) {
                Write-Host ("r{0} final seen, alive after {1}s -> killing" -f $r.rep, $GraceSeconds)
                $r.proc.Kill(); $r.proc.WaitForExit(30000); $rc = 'killed-after-final'; break
            }
            $rc = $r.proc.ExitCode; break
        }
        Start-Sleep -Seconds 10
    }
    if ($null -eq $rc) { $rc = $r.proc.ExitCode }
    $t1 = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    Set-Content -Path "$Log\r$($r.rep).end" -Value $t1 -NoNewline
    Set-Content -Path "$Log\r$($r.rep).rc"  -Value $rc  -NoNewline
    Write-Host ("{0} r{1} rc={2} wall={3}s ndjson={4}B" -f $Model, $r.rep, $rc, ($t1 - $r.t0), (Get-Item $r.nd).Length)
}
Write-Host "CANDIDATE $Model DONE"

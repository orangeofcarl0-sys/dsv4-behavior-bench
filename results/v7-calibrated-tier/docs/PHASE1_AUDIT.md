# Phase 1 — Repository & evidence audit

Date: 2026-10-11 (session continues with omnigate2api/deepseek-v4.1-flash)
Repo: `orangeofcarl0-sys/dsv4-behavior-bench`

## 1. Git state

| item | value |
|---|---|
| `origin/main` HEAD | `86b6adf` "Merge pull request #9 from orangeofcarl0-sys/v241-leaderboard" |
| open PRs | none (PR #9 merged 2026-10-04T19:24:12Z) |
| working tree | clean on `main`; one untracked leftover `bench/gold2/` containing only `__pycache__` (not tracked, no source) |
| local branches | `main`, `v241-leaderboard`, `model-harness-effort` (all previously pushed) |

### Evidence directories on main

| path | contents |
|---|---|
| `results/model-harness-effort/` | first real-model round, **V5 v2.4.0 / 66**, space-bunny-free, n=5 (superseded) |
| `results/model-harness-effort-v241/` | re-run after the errata, **V5 v2.4.1 / 68**, space-bunny-free, n=5 (current) |
| `results/v5-minimal-pilot/` | V5-Minimal information ablation, 9 runs |
| `results/v6-pilot/` | V6 three-task prototype pilot, 12 runs |
| `results/v5_mutation_check.json` | mutation sanity (9/9) |

## 2. Tier inventory

| tier | status | current verdict |
|---|---|---|
| **V1–V4 legacy** (`d10 d11 d12 t2 t3 t4 v4`) | present, frozen, 81 tests | never re-evaluated on the current model population |
| **V5** (`v5/`, v2.4.1) | present, frozen, 68 tests + 33 behaviours | saturated: max level 68/68 x5 |
| **V5-Minimal** (`v5minseed/`) | present | 9/9 runs at 68/68 — information ablation negative |
| **V6** (`v6/taskA_ledger taskB_framecodec taskC_cfgmerge`) | prototype | 9/9 at budget 40; spread only at budget 12 |
| `spec/BENCHMARK_STATUS.md` | present | freeze verdict: **NOT READY** |

## 3. Removed-history inventory (recoverable)

`gold/`, `gold2/`, `grade_v3.ps1` and the pre-cleanup `results/` were removed from main by
PR #4 (`v5-cleanup`). They are recoverable from `aa2d0a8` and were restored for this round to
`ref_aa2d0a8/` (outside the repo).

## 4. Legacy task conditions — restorability

| ingredient | status |
|---|---|
| broken seed `<seed-root>/datapipe` @ `61eff68` | **present**; working tree differs from HEAD only by CRLF (`git diff --ignore-cr-at-eol` empty) |
| v2.3 task book `<seed-root>/ONBOARDING_TODO.md` (3656 B) | **present** |
| v2.3 task prompt | reconstructed verbatim (the copy inside `results/model-harness-effort/harness/` had been overwritten with the v2.4 text; the diff between the two is exactly the two spec references) |
| legacy suites | present and unmodified |

**Conclusion: the old V1–V4 experiment is fully reproducible.** No ingredient was lost.

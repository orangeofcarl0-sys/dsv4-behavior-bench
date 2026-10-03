# LEGACY / SUPERSEDED (V1–V4, datapipe v2.3)

**These results are archived and must not be compared with V5 scores.**

Everything under `results/` that predates the V5 upgrade was produced under a
different benchmark configuration:

| | Legacy (these results) | Current (V5) |
|---|---|---|
| Task spec | datapipe **v2.3** | datapipe **v2.4** |
| Seed | v2.2.1 broken seed (external tag, not in repo) | `v5seed/` (in repo) |
| Scoring | raw `passed / 81` over d10..v4 | `grade_v5.py`, 66 tests + behavior score |
| Suite location | `d10 d11 d12 t2 t3 t4 v4` | `v5/` |

Because the denominator, the task book and the starting seed all changed, a
legacy score of e.g. 79/81 says **nothing** about what that candidate would
score on V5.

## Required action

After the V5 suite is frozen, **all candidates must be re-tested** under the
same blind, one-shot protocol using the v2.4 task book (`spec/ONBOARDING_TODO_v2.4.md`)
and the in-repo seed (`v5seed/`), scored with `grade_v5.py`. Until those runs
exist, the V5 leaderboard is intentionally empty — do not fill it by copying or
rescaling legacy numbers.

## What is preserved here for

- historical record of the V1–V4 methodology iteration;
- regression comparison of the frozen legacy suites (they are unchanged);
- provenance of the calibration that motivated V5 (top saturation at 75–79/81).

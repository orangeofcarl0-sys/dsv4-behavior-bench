# LEGACY / SUPERSEDED (V1–V4, datapipe v2.3)

**The old results and reference baselines have been removed. Do not compare
anything here with V5.**

As part of the V5 upgrade, the following were deleted from the working tree:

- old run results — `results/space-bunny-free-effort-sweep/` (leaderboard +
  reasoning-effort sweep evidence);
- old reference baselines — `gold/` and `gold2/`;
- old grader — `grade_v3.ps1`.

All of them remain retrievable from git history at `aa2d0a8` (the last commit
before V5). They were produced under a different benchmark configuration:

| | Legacy (removed) | Current (V5) |
|---|---|---|
| Task spec | datapipe **v2.3** | datapipe **v2.4** |
| Seed | v2.2.1 broken seed (external tag) | `v5seed/` (in repo) |
| Scoring | raw `passed / 81` over d10..v4 | `grade_v5.py`, 66 tests + behavior score |
| Task book | v2.3 `ONBOARDING_TODO.md` (was not in repo) | `spec/ONBOARDING_TODO_v2.4.md` |

Because the denominator, task book and starting seed all changed, a legacy score
of e.g. 79/81 says **nothing** about how that candidate would score on V5.

## What is kept

The legacy **test suites** `d10 d11 d12 t2 t3 t4 v4` (81 tests) are retained,
frozen and unchanged, for regression comparison and provenance. They are
reported as a separate section by `grade_v5.py` and can be run directly:

```bash
DATAPIPE_REPO=<candidate-repo> python3 -m pytest d10 d11 d12 t2 t3 t4 v4 -q
```

## Required action

After the V5 suite is frozen, **all candidates must be re-tested** under the
same blind, one-shot protocol using the v2.4 task book
(`spec/ONBOARDING_TODO_v2.4.md`) and the in-repo seed (`v5seed/`), scored with
`grade_v5.py`. Until those runs exist the V5 leaderboard is intentionally empty —
do not fill it by copying, rescaling, or cherry-picking deleted legacy numbers.

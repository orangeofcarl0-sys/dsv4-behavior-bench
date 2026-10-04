# V5-Minimal pilot — information ablation result

**Status: experiment complete. Negative result for V5-Minimal; V5 saturation is
NOT primarily an over-specification effect.**

## Design

Clean A/B control (see `spec/V5_MINIMAL.md`):

| held constant | changed |
|---|---|
| seed code (byte-identical to `v5seed`), public tests, tools, sample_data | candidate task book (315-line clause spec → short maintainer brief) |
| hidden `v5/` suite, behavior manifest, `grade_v5.py` | distributed evidence layer (README/CHANGELOG/docs/examples) |
| model, tool permissions (web + subagent off) | — |

Both workspaces grade identically before any model touches them:
seed `17/68` behavior `0.0909`; v5minseed `17/68` behavior `0.0909`.

## Runs

`space-bunny-free`, one-shot blind, 3 effort levels × 3 replicates = 9 runs, each
in its own byte-identical workspace copy.

| run | raw | behavior | legacy | public |
|---|---|---|---|---|
| r1/low | 68/68 | 1.000 | 80/81 | 25/25 |
| r1/medium | 68/68 | 1.000 | 80/81 | 25/25 |
| r1/high | 68/68 | 1.000 | 80/81 | 25/25 |
| r2/low | 68/68 | 1.000 | 80/81 | 25/25 |
| r2/medium | 68/68 | 1.000 | 80/81 | 25/25 |
| r2/high | 68/68 | 1.000 | 80/81 | 25/25 |
| r3/low | 68/68 | 1.000 | 79/81 | 25/25 |
| r3/medium | 68/68 | 1.000 | 80/81 | 25/25 |
| r3/high | 68/68 | 1.000 | 80/81 | 25/25 |

**9/9 runs: V5 raw 68/68, behavior 1.000, public 25/25.**

## Comparison to full-spec V5

Full-spec (`results/model-harness-effort/`, v2.4.0 / 66-test suite):
mean 64.2–65.4 / 66, behavior 0.94–0.98, 7/25 perfect.

V5-Minimal (v2.4.1 / 68-test suite): **9/9 perfect, behavior 1.000.**

Removing the detailed task book did not lower the score at all. If anything the
minimal condition scored *higher* than the full-spec mean (though the suites and
revision differ, so this is not a like-for-like delta — see caveats).

## Reading the traces

The model did not need the task book's checklist because it reconstructed the
contract from the distributed evidence:

- Every run read `ONBOARDING_TODO.md`, `README.md`, `CHANGELOG.md`; 8/9 read the
  full `docs/` set and `examples/`.
- `r1/low` reached 68/68 reading only ONBOARDING + README + CHANGELOG + source,
  then wrote its own `verify_v24.py` (run 8–11 times) and iterated to green —
  it recovered the semantics from the changelog and source alone.
- Tool counts 38–77; the model consistently built its own verification harness,
  which is exactly the "self-verification" behavior the benchmark rewards.

## Caveats

- The full-spec baseline is v2.4.0 / 66 tests; V5-Minimal is v2.4.1 / 68 tests.
  A like-for-like comparison requires re-running full-spec V5 under v2.4.1.
- Same model family across all runs (one model, three effort levels). The
  conclusion "information ablation did not help" is solid for this model; a
  second family would strengthen it.

## Decision (Phase 3 gate)

Per `spec/V5_MINIMAL.md` §7: **V5-Minimal stays saturated → do not extend
datapipe further.** Record V5-Minimal as a completed negative result and move to
the V6 tier. This is the "still saturated" branch of the gate.

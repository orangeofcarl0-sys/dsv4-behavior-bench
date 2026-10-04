# V6 pilot — multi-task inference tier result

**Status: prototype piloted. Top of distribution still saturates at budget 40;
one genuine reasoning failure appears only under a tight budget. NOT READY TO
FREEZE.**

## Design

Three independent micro-repos, short `ISSUE.md`, fixed tool-call budget enforced
by a watchdog (see `spec/V6_PROTOTYPE.md`). Same model (`space-bunny-free`), same
blind one-shot protocol as V5.

Calibration before any model run (hidden-suite behavior score):

| task | ref | seed | seed public |
|---|---|---|---|
| taskA_ledger | 1.000 (9/9) | 0.444 (4/9) | 5/5 pass |
| taskB_framecodec | 1.000 (6/6) | 0.167 (1/6) | 6/6 pass |
| taskC_cfgmerge | 1.000 (7/7) | 0.286 (2/7) | 6/6 pass |

Both seeds pass their public suites, so a model that only runs the public tests
cannot find the deep behaviors.

## Runs — budget 40 tool calls, effort medium, n=3 per task

| task | rep | hidden | behavior | tool calls |
|---|---|---|---|---|
| taskA_ledger | r1 | 13/13 | 1.000 | 29 |
| taskA_ledger | r2 | 13/13 | 1.000 | 25 |
| taskA_ledger | r3 | 13/13 | 1.000 | 18 |
| taskB_framecodec | r1 | 17/17 | 1.000 | 15 |
| taskB_framecodec | r2 | 17/17 | 1.000 | 31 |
| taskB_framecodec | r3 | 17/17 | 1.000 | 23 |
| taskC_cfgmerge | r1 | 17/17 | 1.000 | 16 |
| taskC_cfgmerge | r2 | 17/17 | 1.000 | 15 |
| taskC_cfgmerge | r3 | 17/17 | 1.000 | 13 |

**9/9 runs: behavior 1.000.** No failure signature difference between tasks at
this budget.

## Tight-budget probe (budget 12 tool calls)

Runs killed by the watchdog once the tool-call count exceeded 12:

| task | hidden | behavior | note |
|---|---|---|---|
| taskA_ledger | 13/13 | 1.000 | solved before the cap bit |
| taskC_cfgmerge | 17/17 | 1.000 | solved before the cap bit |
| taskB_framecodec | 13/17 | **0.833** | genuine reasoning failure |

The one non-perfect result is informative: taskB under the tight budget fails
`test_b1_any_split_equivalence` for escape-heavy payloads, `test_b2_escape_split_inside_pair`,
and `test_b4_partial_payload_across_many_chunks`. That is exactly the escape-split
state-machine behavior the task is built to probe — a real reasoning failure, not
a spec ambiguity. It is the only separation observed anywhere in this round.

## Findings

1. **At a generous budget (40), all three V6 tasks saturate** for this model.
   Task structure alone (three different cognitive frames: atomicity,
   state-machine, precedence) did not create separation when the model had room
   to iterate.
2. **Budget is a real lever.** Cutting the budget from 40 to 12 produced the only
   sub-perfect score, on the task whose correct solution requires maintaining
   explicit parser state across chunk boundaries. The failure is a true reasoning
   miss, concentrated in one behavior family.
3. **Failure signatures do differ in principle**: taskB (state machine) is
   measurably harder under budget than taskA/taskC, which are solved quickly.
   This is the first evidence that a task-shape axis separates models where a
   single-task contract does not.

## Freeze gate

Per `spec/V6_PROTOTYPE.md`, V6 is **NOT READY TO FREEZE**:

- [ ] ≥3 real candidates × n≥3 — only one model family piloted;
- [x] no mass ceiling? — **no**: 9/9 at 1.000 at budget 40;
- [~] different failure signatures — only visible under a tight budget;
- [x] failures from reasoning, not ambiguity — the tight-budget taskB failure is
  a reasoning miss.

The promising direction for the next round is not more tasks but a **tighter,
calibrated budget** (the model solves these repos in 13–31 tool calls; a budget
near the low end of that range is where separation lives) plus a second model
family.

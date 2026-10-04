# Benchmark status report — information ablation + V6 prototype

Date: 2026-10-04. Covers the round that (a) ran a clean information ablation of
V5 and (b) built and piloted the V6 multi-task tier. Answers the seven core
questions and states the freeze verdict.

## Baseline

- `main` @ `a086efb`, working branch `v5minimal-v6-experiments`.
- Frozen V5 artifacts (`v5/`, `v5ref/`, `v5seed/`, `spec/ONBOARDING_TODO_v2.4.md`,
  `spec/FROZEN_HASHES.txt`, `grade_v5.py`, `mutation_check.py`): **unmodified**
  (0 frozen-hash mismatches; `git diff HEAD -- <frozen>` empty).
- Reference re-verified: `v5ref` 68/68, behavior 1.000, legacy 80/81, ~18s.
- Mutation sanity: 9/9 caught.

## Q1 — Was V5 saturation "task too easy" or "over-specification"?

**Over-specification is ruled out.** A clean ablation held the seed code
(byte-identical), hidden tests, grader, and tool permissions constant, and
replaced the 315-line clause-by-clause task book with a 36-line maintainer brief
plus a distributed evidence layer. Result: **9/9 runs still scored 68/68
(behavior 1.000).** Removing the checklist changed nothing. The remaining
explanation is the task class itself: for this model, reconstructing and
repairing a single small pipeline contract is solved.

## Q2 — How much did real-model performance drop from full-spec to minimal?

**Not at all.** Full-spec V5 (v2.4.0/66): behavior 0.94–0.98, 7/25 perfect.
V5-Minimal (v2.4.1/68): behavior 1.000, 9/9 perfect. Caveat: the two baselines
are different suite revisions, so this is not a strict like-for-like delta; the
like-for-like statement is that the *information reduction* produced no
measurable degradation.

## Q3 — Which behaviors caused the drop?

None dropped. All 33 behaviors were satisfied in all 9 runs. Traces show the
model rebuilt the contract from `CHANGELOG.md` + `docs/` + source; one run
(`r1/low`) reached 68/68 from the changelog and source alone, writing its own
`verify_v24.py` and iterating to green.

## Q4 — Did information reduction create unfair (underivable) questions?

No. Every one of the 33 behaviors has ≥2 independent candidate-visible sources
(provenance audit in `spec/V5_MINIMAL.md` §4). No run failed a behavior for lack
of evidence; there were no failures at all.

## Q5 — What different abilities do the three V6 tasks test?

- `taskA_ledger` — **atomicity + invariant reasoning**: a rejected write leaves no
  trace; settlement is all-or-nothing; exact integer arithmetic; read isolation.
- `taskB_framecodec` — **state-machine reconstruction**: a byte-stream decoder
  correct under *any* chunking, including splits inside the escape pair and the
  header, plus CRC-failure recovery and resync.
- `taskC_cfgmerge` — **precedence reasoning**: per-leaf merge, falsy-vs-unset,
  `None`-deletes, list replacement, environment typing, immutability.

Each seed passes its public suite while failing its hidden suite (0.17–0.44), so
the three tasks are not merely the same skill reskinned.

## Q6 — Does V6 produce usable score spread for Flash?

**Not at a generous budget.** At 40 tool calls, 9/9 runs scored 1.000 across all
three tasks — no spread. Spread appeared only when the budget was cut to **12
tool calls**: `taskB_framecodec` fell to 0.833 on genuine escape-split
state-machine reasoning, while `taskA`/`taskC` still solved within budget. So the
lever is the **work budget**, not the number of tasks.

## Q7 — Is the benchmark ready to freeze?

**NOT READY TO FREEZE.**

- V5 / V5-Minimal: saturated for the piloted model; keep V5 as a *compliance
  tier*, do not extend datapipe with more same-kind tests.
- V6: only one model family piloted (gate needs ≥3 candidates × n≥3); a mass
  ceiling persists at budget 40; failure-signature differences appear only under
  a tight budget. Next round should calibrate a tighter budget and add a second
  model family before any freeze.

## What changed in the repo this round

| artifact | purpose |
|---|---|
| `spec/V5_MINIMAL.md`, `v5minseed/` | the ablation condition (minimal task book + distributed evidence) |
| `results/v5-minimal-pilot/` | harness, 9 grade JSONs, `RESULT.md` |
| `spec/V6_PROTOTYPE.md`, `v6/` | three micro-tasks (ref/seed/hidden/public), design |
| `grade_v6.py` | V6 grader (fixed expected counts, behavior manifest) |
| `results/v6-pilot/` | harness, 12 grade JSONs, `RESULT.md` |

No frozen V5 artifact was modified; the legacy `d10..v4` suites remain untouched.

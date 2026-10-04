# V6 prototype — multi-task inference tier

Status: **prototype + pilot.** Not frozen. See `spec/V5_MINIMAL.md` for the V5
information-ablation experiment that motivated this.

## Why a separate tier

V5 (and V5-Minimal) is a *single* task: reconstruct one datapipe contract. Even
with the task book ablated to a short issue brief, real Flash runs saturate it.
V6 tests something different and orthogonal:

> Given a small repo, a short production issue, and a **fixed work budget**, can
> the model recover the program's semantics from repository evidence and fix
> non-local problems?

Three independent micro-repos, each exercising a different cognitive structure.
They are Python-stdlib only, ~200–350 LOC of reference, with a small public suite
and a fast hidden grader.

## The three tasks

| task | domain | cognitive structure under test |
|---|---|---|
| `taskA_ledger` | double-entry ledger | **atomicity + invariant reasoning**: a rejected write must leave no trace; settlement is all-or-nothing; exact arithmetic; read isolation |
| `taskB_framecodec` | length-prefixed frame codec | **state-machine reconstruction**: a byte-stream decoder must be correct under *any* chunking, incl. splits inside the escape pair, the header, and across CRC recovery |
| `taskC_cfgmerge` | layered configuration | **precedence reasoning**: per-leaf merge, falsy-vs-unset, `None`-deletes, list replacement, env typing, immutability |

Each task's candidate-visible material is a short `ISSUE.md` plus the repo's own
README, docs, and public tests. No task book states the full contract; the
contract is distributed and must be reconstructed.

## Calibration (synthetic, pre-pilot)

Hidden-suite behavior score, reference vs. seed:

| task | ref | seed | public (seed) |
|---|---|---|---|
| taskA_ledger | 1.000 (9/9) | 0.444 (4/9) | 5/5 pass |
| taskB_framecodec | 1.000 (6/6) | 0.167 (1/6) | 6/6 pass |
| taskC_cfgmerge | 1.000 (7/7) | 0.286 (2/7) | 6/6 pass |

Both seeds **pass their public suites** — the public suite is blind to the deep
behaviors by construction, so a model that only runs the public tests and stops
will not find them.

## Work budget

The pilot fixes a tool-call budget (default 30–40, `run_v6.sh MAX`) enforced by a
watchdog that kills a run when its tool-call count exceeds the cap. Rationale:
without a bound, an agent with unlimited retries eventually saturates any small
task; the benchmark is meant to measure *how much correct semantics can be
recovered within a limited engineering budget*, not *whether it finishes given
unlimited attempts*. Wall-clock is deliberately not used (provider latency would
contaminate comparisons).

## Provenance audit

Every hidden behavior is tagged in each task's `hidden/behavior_manifest.json`:

- `explicit-issue-requirement` — stated in the task's `ISSUE.md`;
- `repository-derived-contract` — derivable from README/docs/format spec;
- `backward-compatibility` — behavior the existing code/tests already imply;
- `general-invariant` — a property (e.g. immutability, conservation) that any
  correct implementation of the stated semantics must have.

No behavior is justified by "the reference does it this way". The `ISSUE.md`
files list *symptoms*, never the fix.

## Freeze gate (not yet met)

Per the design discipline for this tier, V6 is not frozen until:

1. at least 3 real Flash candidates have been piloted, each n ≥ 3;
2. the top of the distribution is not a mass ceiling (no majority at ~100%);
3. the three tasks produce **different** failure signatures;
4. failures come from reasoning, not spec ambiguity.

Until then this directory is a prototype and its scores are experimental.

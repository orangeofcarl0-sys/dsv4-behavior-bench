# V5-Minimal — information ablation of the datapipe v2.4 benchmark

Status: **experimental candidate-information condition.** Not a new score column
and not a replacement for V5. It shares V5's seed, hidden tests and grader; only
the *candidate-visible information* differs.

## 1. Question this exists to answer

The V5 / v2.4.0 real-model sweep (`results/model-harness-effort/`) showed
`space-bunny-free` at a mean of 64.2–65.4 / 66 (behavior 0.94–0.98) across five
reasoning-effort levels, with no usable separation between levels. That is a
ceiling. The two competing explanations:

1. **The task is easy** — Flash-class models can already reconstruct and repair
   this pipeline.
2. **The task book is over-specified** — `spec/ONBOARDING_TODO_v2.4.md` reads
   like an implementation checklist (it states the operator order, the exact
   `DataError` inheritance rule, the `temp=0` fallback rule, the skip/fail
   duality, the malformed/invalid/null taxonomy, and even which manual
   verifications to perform). Reading it and transcribing it is most of the work.

V5-Minimal isolates explanation 2 with a clean A/B: **same task, same seed, same
hidden semantics, same grader — full spec vs. minimal spec.**

## 2. What is held constant (the control)

| element | full-spec V5 | V5-Minimal |
|---|---|---|
| candidate code (`datapipe/`) | `v5seed/datapipe` | `v5minseed/datapipe` — **byte-identical** (verified) |
| public tests / tools / sample_data | `v5seed/*` | byte-identical (verified) |
| hidden tests (`v5/`) | frozen | **unchanged** |
| behavior manifest | frozen | **unchanged** |
| grader (`grade_v5.py`) | frozen | **unchanged** |
| tool permissions | web + subagent disabled | identical overlay |
| work budget | unbounded one-shot | unbounded one-shot |

The only changed variable is the candidate's visible information: the task book
plus a distributed evidence layer.

## 3. What changed

### 3.1 Task book

`v5minseed/ONBOARDING_TODO.md` replaces the 315-line clause-by-clause spec with a
short maintainer brief: background, five user-reported symptoms, goals and hard
constraints. It deliberately omits (per design principle A4):

- the processing-order diagram;
- the `DataError`-must-not-subclass-`ValueError` rule (moved to API docs, where
  it is *justified* rather than dictated);
- the `temp=0` / `temp=""` / `temp=null` fallback enumeration;
- the malformed vs. invalid vs. `null` taxonomy;
- the skip/fail strict-duality statement;
- the atomic-output required end-state example;
- the list of manual verifications to perform.

### 3.2 Distributed repository evidence

The same contract is now recoverable from ordinary engineering artifacts, none of
which alone contains the whole answer:

| artifact | carries |
|---|---|
| `README.md` | stage overview, exit-code table, docs index, "known issues" |
| `CHANGELOG.md` | per-version behavior; v2.4 in-progress clause list; explicit intentional change of the 2.3 skip→exit-1 behavior; the `temp=0` bug; **stale pre-2.4 notes that are explicitly superseded** |
| `docs/architecture.md` | the operator order, "filter before unit", "dedupe keeps last", CLI-is-a-wrapper equivalence, a stale note corrected by the changelog |
| `docs/error-policy.md` | skip/fail, the three buckets, usage-vs-data errors, counting, atomicity |
| `docs/data-model.md` | aliases, `temp=0` no-fallback, typing, non-finite rule, ranges, dedupe key, idempotence, representation independence |
| `docs/filters.md` | operators, whitespace, AND commutativity, malformed-filter-is-usage-error |
| `docs/emit.md` | csv quoting, md escaping + arithmetic mean, stats semantics |
| `docs/api.md` | signatures, `DataError` not a `ValueError` (with rationale), library/CLI parity |
| `examples/README.md` | worked commands with expected output, incl. skip=exit 0 and fail=exit 1+no file |
| `tests/public/` (13 failing) | an executable statement of many v2.3 behaviors the upgrade regressed |

### 3.3 Stale-evidence test

`CHANGELOG.md` and `docs/architecture.md` both retain the pre-2.4 statement that
a skipping `transform` returns status 1, each explicitly marked as superseded and
resolved by a dated precedence rule ("the newest released version wins"). This
tests repository reasoning: the answer is determinate, but only if the candidate
reads for version precedence instead of trusting the first line it finds. No
genuinely unresolvable conflict was introduced.

## 4. Provenance audit

Every one of the 33 hidden behaviors must be derivable from candidate-visible
evidence — never from "the reference does it this way". Evidence is cited as
`artifact §section`. Behaviors are named as in `v5/behavior_manifest.json`.

### contract

| behavior | evidence |
|---|---|
| `on_error_default_skip` | CHANGELOG v2.4.0 ¶1; error-policy §Two modes; examples §2 |
| `skip_exit_zero` | CHANGELOG v2.4.0 ¶2; README exit table; error-policy §Two modes; examples §2 |
| `fail_raises_data_error` | error-policy §Two modes; api §Errors |
| `fail_cli_exit_one` | README exit table; error-policy §Two modes; examples §3 |
| `atomic_output` | CHANGELOG v2.4.0 ¶3; error-policy §Atomicity; emit §Output is atomic; examples §3 |
| `usage_vs_data_error` | README exit table; error-policy §Errors that are not policy events; filters §A filter is not a policy event; api §Errors |
| `multiple_filter_and` | CHANGELOG v2.4.0 ¶4; filters §Multiple filters; examples §4 |
| `pipeline_ordering` | architecture §Operator ordering is observable; filters §Filters and unit conversion |

### interaction

| behavior | evidence |
|---|---|
| `composite_normalization_dedupe` | data-model §Timestamps, §Dedupe |
| `ordering_dedupe_filter_unit` | architecture §Operator ordering; data-model §Dedupe; filters §Multiple filters |
| `cross_module_legacy` | data-model §Field aliases; examples §6 |
| `cli_chain` | README §Quickstart; architecture §The CLI is a wrapper; examples §1 |
| `representation_roundtrip` | data-model §Representation independence |

### adversarial

| behavior | evidence |
|---|---|
| `malformed_policy_skip` | error-policy §What counts as bad (row 1) |
| `malformed_policy_fail` | error-policy §Two modes (duality) |
| `metric_coercion` | data-model §Metric typing, §Field aliases; error-policy table row 3 |
| `non_finite_rejection` | CHANGELOG v2.4.0 ¶6; data-model §Metric typing; error-policy table row 2 |
| `error_classification` | README exit table; error-policy §Errors that are not policy events; filters §A filter is not a policy event |
| `atomicity_fail` | error-policy §Atomicity; emit §Output is atomic |
| `library_cli_parity` | api §Equivalence with the CLI; architecture §The CLI is a wrapper |

### boss

| behavior | evidence |
|---|---|
| `boss_malformed_policy` | error-policy §Two modes, §Atomicity |
| `boss_identity_normalization` | data-model §Timestamps, §Dedupe |
| `boss_ordering` | architecture §Operator ordering; filters §Filters and unit conversion |
| `boss_legacy_metrics` | data-model §Field aliases; examples §6 |
| `boss_formats_roundtrip` | emit §CSV, §Markdown; data-model §Representation independence |
| `boss_cli_chain` | examples §1, §4, §5, §7; README exit table |
| `boss_atomicity` | error-policy §Atomicity |
| `boss_parity` | api §Equivalence with the CLI |

### metamorphic

| behavior | evidence |
|---|---|
| `timestamp_idempotence` | data-model §Timestamps ("Normalization is idempotent") |
| `format_equivalence` | data-model §Representation independence |
| `filter_invariance` | filters §Whitespace, §Multiple filters (commutativity) |
| `dedupe_representation_invariance` | data-model §Dedupe, §Representation independence |
| `conservation` | error-policy §Counting |

**Result: 33/33 behaviors have at least one candidate-visible source, and no
behavior relies on the reference implementation as its only justification.**
Behaviors with two or more independent sources: 33/33 (a spec/doc statement plus
either an example or a changelog entry).

## 5. Fairness guard

If a pilot shows a behavior failing because it is genuinely *not* derivable, the
fix is to add repository evidence (design option A6/方法 1), never to relax the
hidden test and never to add a targeted hint. Adding evidence is recorded here
and the benchmark is re-piloted; the frozen `v5/` suite is not edited.

## 6. Blinding

The candidate workspace contains no reference to the benchmark: no `v5/`,
`v5ref/`, `behavior_manifest`, `grade_v5`, or repo name. Verified by the same
scan `prep_v5.sh` runs. `v5minseed/` lives only in the host repo, never in the
candidate's copy of the workspace beyond its own contents.

## 7. Decision gate (Phase 3)

- If V5-Minimal restores separation (no mass ceiling, failures spread across
  behavior families, model/effort signatures differ): keep it as the **fast
  Flash benchmark**, and keep full-spec V5 as a separate **compliance tier**.
- If it stays saturated: stop extending datapipe, record V5-Minimal as a
  negative result, and move to V6.

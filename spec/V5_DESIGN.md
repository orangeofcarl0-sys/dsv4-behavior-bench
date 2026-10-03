# V5 Design — datapipe v2.4 behavior benchmark

This document freezes the **why** behind the V5 upgrade. It is the design record
required by the task; the task text itself (what candidates see) is
`spec/ONBOARDING_TODO_v2.4.md`.

## 1. Baseline (before V5)

- Repo `orangeofcarl0-sys/dsv4-behavior-bench`, branch `main`, HEAD `aa2d0a8`, clean.
- Legacy suite: `d10(11) d11(11) d12(10) t2(8) t3(6) t4(11) v4(24)` = **81 tests**,
  零依赖 pytest, `< 4 s` per candidate repo.
- `gold2` (v2.3-complete reference) = 81/81; `gold` (GOLD) = 76/81.
- Strong Flash candidates already reach 75–79/81; the ceiling is saturated.

**Ceiling causes (audited):**

1. Most tests are single-point edge cases (`microsecond preserved`, `whitespace
   trimmed`, `BOM works`, `malformed line skipped`).
2. The same semantic is covered by many tests: malformed-NDJSON alone appears in
   `t2`, `t4a`, `v4/test_v4.py` (×2), `v4/test_v4core.py` (×2) — one defect costs
   5+ raw points, so raw `/81` carries implicit repetition weighting.
3. The hardest items are local corner cases, not global pipeline consistency.
4. `gold2` was completed by iterating until tests passed, so "GOLD says so" had
   become the de-facto spec.
5. The v2.3 `ONBOARDING_TODO.md` (the actual task book) was **not in the repo**,
   and neither was the v2.2.1 broken seed — the experiment was not reproducible
   from the repository alone.

## 2. V5 design goals

Keep the positioning: a **small, fast, one-shot Flash-level** repair task.
Change the axis of difficulty from *"many local edge cases"* to
*"a few new contracts × non-local composition × consistency × error policy ×
atomicity"*.

- Do **not** add: SQL/expression language, async, networking, DB, plugin
  framework, YAML config, LLM judge, subjective style scoring.
- Keep stdlib-only pytest; whole grader ideally < 20 s.

### v2.4 contract additions (frozen)

1. `--on-error skip|fail` (default `skip`), CLI + library.
2. Atomic output under `fail` (absent stays absent; existing keeps old content).
3. Repeated `--filter` with AND semantics; frozen processing order
   `parse/normalize → validation → dedupe → filter(s) → unit → emit`.

### Backward compatibility

`--on-error` defaults to `skip`; `filter_expr=` single-arg calls still work;
v2.3 normalization/dedupe/filter/unit/emit semantics are preserved. The **one
intentional change** is CLI `transform` exit code: v2.3 returned 1 when records
were skipped; v2.4 explicitly returns 0 (skip is success). This supersedes the
legacy `d12::test_d127_cli_transform_malformed_exit1`, which the reference is
expected to fail; it is recorded here rather than silently edited (legacy tests
stay frozen for historical comparability).

## 3. Difficulty calibration (measured)

| Subject | V5 raw | V5 behavior | Legacy raw | Notes |
|---|---:|---:|---:|---|
| `v5ref` (v2.4 reference) | 66/66 | 1.000 | 80/81 | only d127 (intended supersession) |
| `gold2` (v2.3-complete) | 35/66 | 0.469 | 81/81 | models a competent v2.3 solver |
| `gold` (v2.3 GOLD) | 33/66 | 0.438 | 76/81 | |
| `v5seed` (broken baseline) | 17/66 | 0.094 | 37/81 | no accidental mass-passing |

`gold2` at 35/66 raw and 47% of behaviors shows the suite separates "implemented
v2.3" from "understood v2.4" without any hidden knowledge: a solver that lands
between the two bookends (as a real Flash candidate would) scores in the 50–80%
raw band.

## 4. Test matrix

| Suite | Count | Role |
|---|---:|---|
| `v5/core` | 19 | Explicit v2.4 contract clauses (§3–§9). |
| `v5/interaction` | 8 | Cross-module consistency, operator ordering, multi-constraint composition. |
| `v5/adversarial` | 19 | Error classification, bad input, atomicity, representation edges. |
| `v5/boss` | 11 | High-density end-to-end composite scenarios (B1–B11). |
| `v5/metamorphic` | 9 | Deterministic invariants (idempotence, representation/order invariance, conservation). |
| **V5 total** | **66** | |
| legacy `d10..v4` | 81 | Frozen, reported separately for historical comparability. |

Metamorphic tests use `random.Random(seed)` only (stdlib, fixed seeds) — no
Hypothesis, no third-party deps.

## 5. Semantic behavior manifest

`v5/behavior_manifest.json` maps 32 behaviors → their tests. Scoring:

- A behavior is **satisfied only when all its tests pass**.
- Category score = satisfied / total behaviors in the category.
- Overall behavior score = mean of the five category scores (transparent, fixed).
- Raw `passed/total` is still reported for debugging.

This directly fixes the "one malformed-NDJSON defect costs many points" problem:
redundant tests for the same behavior collapse into one behavior.

Provenance tags (per behavior): `explicit-v2.4-contract`,
`backward-compatibility`, `cross-module-invariant`, `robustness-policy`.
No behavior is justified by "GOLD does it".

## 6. Seed design

`v5seed` is a plausible-but-wrong v2.4 attempt — not an empty skeleton. It carries
the documented pre-v2.3 defects plus the realistic v2.4 traps from the design:

- `row.get("temp") or row.get("temperature")` → wrong on `temp=0`;
- broad `except Exception` → swallowed program errors counted as skips;
- eager, interleaved output writes → partial output on failure;
- CLI accepts `--on-error` but never threads it to the library;
- multiple `--filter` parsed but only the last applied;
- filters run before dedupe / after unit conversion (ordering bugs).

It scores 17/66 raw, 9.4% behavior — low without relying on "missing feature =
zero".

## 7. Grader

`grade_v5.py`:

- Fixed per-suite expected counts; a shortfall or collection error marks the
  suite **invalid** and counts missing tests as failures — the denominator never
  shrinks.
- Detects collection/import errors explicitly (pytest exit 2/3/4 or `errors > 0`),
  not by regex-scraping "X passed".
- Emits machine-readable JSON; computes the behavior score; has no dependency on
  any file inside the candidate workspace.
- Does not read candidate hidden files; only `DATAPIPE_REPO` on `PYTHONPATH`.

## 8. Mutation sanity

`mutation_check.py` applies 8 single-source mutations to `v5ref` and confirms the
behavior score drops for each (see `results/v5_mutation_check.json`):

| Mutation | behavior | raw |
|---|---:|---:|
| only_last_filter | 0.844 | 60/66 |
| filter_after_unit | 0.875 | 62/66 |
| fail_as_skip | 0.906 | 63/66 |
| partial_output | 0.969 | 65/66 |
| temp_or_temperature | 0.938 | 63/66 |
| broad_except | 0.938 | 63/66 |
| dedupe_keep_first | 0.750 | 58/66 |
| skip_exit_one | 0.969 | 65/66 |

All 8 caught. Baseline reference: 66/66, behavior 1.000.

## 9. Duplicate-weight audit

Audit of `v5/behavior_manifest.json`:

- No test id is mapped to more than one behavior (remapping would be the only way
  raw redundancy could leak into the score).
- Within a category, each behavior has weight `1/N`; every category has weight
  `1/5` in the overall score. Test count per behavior therefore does **not** change
  its weight: a behavior covered by 6 tests counts exactly as much as one covered
  by 1.
- Concretely, the legacy problem ("one malformed-NDJSON defect covered by t2,
  t4a, v4×2, v4core×2") is gone: in V5 the malformed-input policy is a single
  behavior per policy branch, and its several tests collapse into one weight.

| Category | Behaviors | Tests mapped | Raw tests would have weighted |
|---|---:|---:|---|
| contract | 8 | 19 | 2.4× over |
| interaction | 5 | 8 | 1.6× over |
| adversarial | 6 | 19 | 3.2× over |
| boss | 8 | 11 | 1.4× over |
| metamorphic | 5 | 9 | 1.8× over |

The right-hand column is what raw `/66` would have done; the behavior score
removes it.

## 10. Development record — correction types

Per the task's requirement to distinguish corrections, this section records the
non-obvious ones:

- **spec correction:** none after freeze. The processing order was confirmed
  against the actual v2.3 code semantics (`validation → dedupe → filter → unit`)
  before freezing, so no post-hoc change was needed.
- **test corrections (during development, before freeze):**
  - `test_i3_validation_before_dedupe`: initially asserted the out-of-range last
    duplicate caused the whole key to vanish; the frozen order (validation before
    dedupe) means the earlier valid row survives. Test corrected to match the
    spec, not the other way round.
  - `test_m7_skip_totals_conserved`: initially undercounted the skipped records
    (forgot the non-object record). Corrected invariant.
  - `test_a2/a3/atomicity`: changed `pytest.raises(Exception)` →
    `pytest.raises(DataError)` so a crashing seed cannot pass by accident.
  - `test_c9_library_filters_list_and`: data adjusted so a last-filter-only
    implementation actually differs from AND.
- **reference implementation bug:** none found; the reference was written from
  the spec and passed the full V5 suite on first run.

## 10. Frozen hashes

Hashes of the frozen artifacts are recorded in `spec/FROZEN_HASHES.txt` after the
final commit. Formal candidate evaluation must not modify the tests after freeze.

## 11. Remaining risks / policy choices

- `--on-error` default `skip` and the v2.3→v2.4 exit-code change are **policy
  choices**: a candidate that keeps v2.3's exit-1-on-skip loses one legacy point
  and one V5 core behavior. This is deliberate and documented.
- `DataError` not subclassing `ValueError` is a policy choice for clean CLI error
  classification; tested directly (`test_c8`).
- Discrimination against real Flash models is **not yet measured here** — the
  calibration above uses `gold`/`gold2` as stand-ins. Formal leaderboard runs
  should start only after this suite is frozen.

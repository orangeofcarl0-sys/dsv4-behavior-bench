# Phase 3 + V7 — probe pool, calibrated tier, and the pilot verdict

Date: 2026-10-11 · status: **V7 NOT FROZEN**

## 1. Deliverables this round

| artifact | what it is |
|---|---|
| `probe_pool.json` | 28 probes (24 legacy semantic behaviours + 4 closure/observe) with provenance and measured verdicts |
| `bench/v7/` | the calibrated tier: 10 behaviours, one file each, three weight tiers |
| `bench/grade_v7.py` | behaviour-level weighted grader |
| `bench/v7/ONBOARDING_TODO.md` | the V7 task book = v2.3 + the two spec fixes |
| `bench/v7/behavior_manifest.json` | behaviour -> tests, weights, provenance, `anchor`, and post-pilot verdicts |
| `V7_DESIGN.md` | design rationale and open items |
| this file | consolidated results |

Nothing existing was modified: V1–V4, V5, V5-Minimal, V6 and all prior `results/` are untouched.

## 2. The probe pool (Phase 3)

28 probes, every one carrying its measured verdict rather than an assumed one:

| verdict | count | disposition |
|---|---:|---|
| live | 8 | candidate main score |
| noise | 4 | regression |
| ceiling | 10 | regression |
| floor-spec-gap | 2 | excluded — the visible contract never stated the rule |
| unmeasured (new closure probes) | 4 | deferred to a later round |

Built from the legacy behaviours directly, not by inventing new feature surface.

## 3. The two spec gaps, and what fixing them revealed

The legacy suite had a 7-item floor cluster (p=0.06, **zero** between-model variance).
Reading the visible task book settled why: the filter/unit interaction order and md pipe
escaping were **never stated**. Six model families all implemented the other reading.

I published both rules in the V7 task book, then ran a fresh pilot (3 families x n=2, 6 runs).

**Result: all three rule-dependent behaviours went from p=0.06 to p=1.00.**

| behaviour | under the unstated rule | under the published rule |
|---|---:|---:|
| `filter_unit_order` | 0.06 | **1.00** |
| `md_table_escaping` | 0.06 | **1.00** |
| `cli_full_chain` | 0.06 | **1.00** |

Every model passes them now. **In neither state do they measure capability**: before, they
measured whether a model guessed an unpublished rule; after, nothing at all.

This is the sharpest finding of the round, and it generalises:

> a hidden item whose rule cannot be derived from the visible contract produces scores that
> look like difficulty and behave like a coin flip. Fixing the contract does not make the
> item discriminating — it deletes it.

It also means the legacy suite's 7 floor items were **not** the "hard semantics" the brief
§1.4 suspected. They were noise wearing difficulty's clothes.

## 4. V7 as it now stands (post-pilot)

5 scored behaviours, 5 demoted to regression:

| behaviour | tier | pilot p | var_between | var_within | verdict |
|---|---|---:|---:|---:|---|
| `whitespace_trimming` | basic | 0.67 | 0.333 | 0.000 | **live** |
| `timestamp_microseconds_preserved` | inference | 0.50 | 0.250 | 0.167 | **live** |
| `bool_is_not_numeric` | inference | 0.50 | 0.250 | 0.167 | **live** |
| `legacy_temperature_fallback` | inference | 0.33 | 0.083 | 0.333 | noise |
| `nonfinite_rejected` | inference | 0.50 | 0.000 | 0.500 | noise |
| `cli_exit_codes` | regression | 1.00 | 0 | 0 | ceiling |
| `csv_dialect_robustness` | regression | 1.00 | 0 | 0 | ceiling |
| `cli_full_chain` | regression | 1.00 | 0 | 0 | ceiling |
| `filter_unit_order` | regression | 1.00 | 0 | 0 | ceiling |
| `md_table_escaping` | regression | 1.00 | 0 | 0 | ceiling |

Anchors under the final scored set: **seed 0.000, gold 0.778, gold2 1.000**.

### Pilot scores (3 families x n=2)

| candidate | r1 | r2 | mean |
|---|---:|---:|---:|
| hy4-preview-f | 0.778 | 0.556 | **0.667** |
| deepseek-v4.1-flash | 0.556 | 0.778 | **0.667** |
| minimax-m3 | 0.000 | 0.222 | **0.111** |

## 5. Honest assessment: V7 is not yet a better benchmark

I have to report the failure alongside the success.

**What works:** the tier separates minimax-m3 (0.111) from the two strong families (0.667)
cleanly, with 5 behaviours instead of 81 tests, and every behaviour has a stated anchor and a
visible-contract basis.

**What does not work:**

1. **The two strong families are tied** (0.667 both) — V7 currently has no resolution in the
   band that matters most.
2. **Within-model variance is still high.** `nonfinite_rejected` has var_within 0.500 against
   var_between 0.000: it flips between runs and separates nobody. Scored behaviour count is
   down to 3 genuinely live items, which is too few to carry a ranking.
3. **Absolute scores are not comparable across task-book revisions.** The same artifacts
   scored 0.10–0.60 under the old book and the fresh runs scored 0.00–0.78 under the fixed
   one. Any published number must state its task-book revision.

**The structural problem this reveals:** removing the false difficulty removed most of the
signal. Legacy's apparent 19.3-point spread was built partly on items that were guessing
lotteries. The genuine, contract-derivable discrimination among current Flash models appears
to be genuinely thin — concentrated in trimming, numeric precision, and type strictness.

That is a real answer to the brief's §20 question, and it is closer to **situation B** than
the raw legacy numbers suggested: once spec gaps are excluded, current Flash models are much
closer together than 52–71/81 implied.

## 6. Recommendation before any freeze

**NOT READY TO FREEZE** (consistent with `spec/BENCHMARK_STATUS.md`).

1. **Grow the live set honestly.** 3 live behaviours cannot rank 6 families. The candidates
   are the noise behaviours (fix their probe design to reduce run variance) and new
   *contract-derivable* closure probes — not new spec-gap items.
2. **Add a second task family** built with the same selection procedure. All current V7
   behaviours live on the datapipe task that every model has now seen repeatedly.
3. **Fix `nonfinite_rejected`** — var_within 0.5 means the probe shape is unstable, not that
   models are inconsistent.
4. **Re-run the full population** (6 families x n=3 = 18 runs) against the fixed task book
   before quoting any V7 leaderboard. The pilot is 6 runs and the two leaders are tied.
5. **Do not discard the legacy suite.** With spec gaps excluded it is the best-calibrated
   instrument the project has; V7 is a re-weighting of its live core, not a replacement.

# V7 — Calibrated Flash Discrimination Tier (design + first measurement)

Date: 2026-10-11 · status: **pilot running, NOT frozen**

## 1. Position in the repo

| tier | role | status |
|---|---|---|
| V1–V4 legacy (81 tests) | historical; **the only tier with measured discrimination** | frozen, untouched |
| V5 / v2.4.1 (68 tests) | **compliance tier** — saturated for Flash | frozen, untouched |
| V5-Minimal | information-ablation control | frozen, untouched |
| V6 prototype | inference prototype | frozen, untouched |
| **V7** | **calibrated discrimination tier** | new, this round |

Nothing existing was modified. V7 is additive.

## 2. Design rules actually applied

1. **Item selection is driven by measurement, not by coverage.** V7's scored set was chosen
   from Phase-2 item statistics over 6 model families, not from "what a pipeline ought to do".
2. **One behaviour per file, behaviour-level scoring.** A behaviour counts only when every
   test in its file passes. This removes the legacy repetition weighting measured in Phase 3
   (`ndjson_malformed_tolerance` had 7 of 81 tests for one behaviour).
3. **Three explicit weights, fixed and public** (basic 1 / inference 2 / hard 3). No per-test
   duplication to buy weight, no black-box weighting.
4. **Kept visible-information level at v2.3**, not the V5 clause-by-clause book: V5-Minimal
   already showed that adding specification removes the inference space.
5. **Two spec gaps closed** in the V7 task book:
   - the filter/unit interaction order (was two unlinked bullets; measured p=0.06 with
     **zero** between-model variance — the legacy suite was scoring an unpublished rule);
   - md table pipe escaping (same situation).
6. **Ceiling behaviours are demoted, not kept for coverage.**

## 3. Validation against the reference anchors

`grade_v7.py` against the three restored references:

| object | V7 score | behaviours satisfied |
|---|---:|---:|
| seed (unfixed v2.2.1) | **0.000** | 0 / 10 |
| gold (v2.3 GOLD) | **0.722** | 8 / 10 |
| gold2 (v2.3 complete) | **1.000** | 10 / 10 |

This is *not* offered as evidence of difficulty — the brief's §23 forbids that inference, and
V5 already proved it wrong. It only shows the tier is anchored.

One useful detail: gold fails `bool_is_not_numeric`, making it one of only two behaviours that
separate gold from gold2. That is the measured top of the difficulty band.

## 4. First measurement on real candidates

V7 was run on the **18 artifacts already produced in Phase 2** — same agent runs, so this is a
like-for-like comparison of the two scoring schemes on identical work.

| metric | V7 (8 scored behaviours, weighted) | legacy (81 tests, raw) |
|---|---:|---:|
| between-model spread | **35.0** | 19.3 |
| mean within-model sd | 7.7 | **3.1** |
| between/within ratio | 4.52 | **6.32** |
| per-run correlation | **r = 0.870 over 18 runs** | — |
| rank concordance | 14 / 15 candidate pairs | — |

Per-model (V7 score x100, then legacy /81):

| candidate | V7 | legacy |
|---|---:|---:|
| deepseek-v4.1-flash | 45.0 | 68.3 |
| hy4-preview-f | 43.3 | 71.3 |
| grok-4.7 | 35.0 | 63.3 |
| gemini-3.5-flash | 31.7 | 60.3 |
| minimax-m3 | 16.7 | 54.3 |
| kimi-k2.6 | 10.0 | 52.0 |

### What this says, including the inconvenient part

- V7 **doubles the between-model spread** (35.0 vs 19.3) using **8 behaviours instead of 81
  tests**, and agrees with legacy at r=0.87 — the two are measuring the same underlying
  ability, which is the sanity check that matters.
- **But V7 is noisier**: within-model sd 7.7 vs 3.1, so the between/within ratio is *worse*
  (4.52 vs 6.32). A coarser scale means one flipped test moves 10% of the score.
- Honest reading: **behaviour-level scoring trades repetition bias for variance.** V7 is not
  yet a strict improvement — it is a better-shaped signal that needs variance control.

### Where the variance comes from (measured)

| behaviour | p | var_between | var_within |
|---|---:|---:|---:|
| `whitespace_trimming` | 0.67 | 0.267 | 0.000 |
| `bool_is_not_numeric` | 0.39 | 0.241 | 0.056 |
| `legacy_temperature_fallback` | 0.28 | 0.196 | 0.056 |
| `nonfinite_rejected` | 0.56 | 0.163 | **0.167** |
| `timestamp_microseconds_preserved` | 0.22 | 0.163 | 0.056 |
| `cli_full_chain` | 0.06 | 0.019 | 0.056 |
| `filter_unit_order` | 0.06 | 0.019 | 0.056 |
| `md_table_escaping` | 0.06 | 0.019 | 0.056 |
| `cli_exit_codes` | **1.00** | 0.000 | 0.000 |
| `csv_dialect_robustness` | **1.00** | 0.000 | 0.000 |

Two consequences, both applied to the manifest:

1. `cli_exit_codes` and `csv_dialect_robustness` passed **18/18** runs — ceiling, demoted to
   regression. They were costing 2 of 20 weight for zero discrimination.
2. `nonfinite_rejected` is the largest within-model variance source (0.167). A behaviour whose
   tests disagree between runs is a probe-design problem, not a model difference; it needs
   more independent probes, not more weight.

### Correction to my own Phase-3 speculation

Phase 3 proposed promoting the operator-ordering cluster as *hard* on the theory that it was
deep. Measuring V7 end-to-end shows those items are still at p=0.06 with between-variance
0.019 — **even after the rule is published they may not become live.** The three
spec-dependent behaviours are therefore marked **UNMEASURED**, not scored-as-hard, until the
pilot returns data. Their Phase-2 numbers came from candidates who never saw the rule and must
not be reused.

## 5. Deliberately NOT in V7

- No new task, no new seed, no new repository. V7 scores the same datapipe task as V1–V4.
- No work-budget lever (brief §15). No tool-call cap is used to manufacture spread.
- No per-test duplication for weight.
- `stop_decision_depth` is recorded as an **observe-only** metric, never scored. It was visible
  in Phase 2 (kimi-k2.6: 516 / 57 / 77 steps across identical runs) and deserves its own line
  rather than being folded into a capability score.

## 6. Open items before any freeze

1. The pilot must resolve the three UNMEASURED behaviours.
2. Within-model variance must come down (target: between/within >= 6, matching legacy) —
   likely by adding *independent* probes per behaviour rather than more tests of one shape.
3. The calibration/holdout split (brief §12) is still undefined; with current model
   availability the honest position is that all six families used here are calibration and any
   future model is out-of-sample.
4. V7 currently reuses the v2.3 datapipe seed. That is a strength (already calibrated) and a
   risk (models have seen this task family). A second task family built with the same
   selection procedure is needed before V7 is a tier rather than a probe set.

# Phase 3 — Probe pool with provenance and calibrated verdicts

Date: 2026-10-11

## 1. What this is, and what it deliberately is not

The brief asks for a 60–120 item probe pool. Phase 2 showed that the legacy suite's
discrimination comes from a **small number of live behaviours**, and that the rest is
padding. Bulk-generating 100 items first and filtering later would reproduce exactly
the failure V5 already demonstrated. So this pool is built the other way round:

> every probe is a **semantic behaviour**, and each carries its measured Phase-2 verdict.
> Nothing enters the pool without knowing whether it is live.

**28 probes**, all sourced from measured behaviour, none invented to pad a count.

| verdict | count | meaning | disposition |
|---|---:|---|---|
| **live** | 8 | 0.15 < p < 0.90 and between-model variance > within-model | **candidate main score** |
| noise | 4 | between-model means close, run-to-run flips dominate | regression only |
| ceiling | 10 | no run ever failed it | regression only |
| **floor-spec-gap** | 2 | p <= 0.10 because the visible spec never states the rule | **excluded; needs a spec fix or deletion** |
| unmeasured | 4 | new closure/observe probes, not yet piloted | pending Phase 4 |

## 2. The live eight (the actual discrimination tier)

| probe | legacy tests | p | D |
|---|---:|---:|---:|
| `whitespace_trimming` | 3 | 0.67 | very high (zero within-model variance) |
| `bool_is_not_numeric` | 1 | 0.39 | 4.33 |
| `legacy_temperature_fallback` | 2 | 0.28 | 3.53 |
| `csv_dialect_robustness` | 6 | 0.78 | 2.93 |
| `cli_full_chain` | 6 | 0.25 | 2.43 |
| `timestamp_microseconds_preserved` | 2 | 0.44 | 1.87 |
| `nonfinite_rejected` | 3 | 0.58 | 1.37 |
| `cli_exit_codes` | 5 | 0.89 | 1.33 |

Note the shape: these are **not** exotic corner cases. They are ordinary contract details
(field trimming, boolean-vs-number, legacy field fallback, CSV quoting, exit codes) that
competent models still get wrong at rates between 25% and 78%.

## 3. Correction: the "floor cluster" is a spec gap, not a deep behaviour

Phase 2 §3.2 speculated that the operator-ordering cluster (4 items, p=0.06) might be a
deep non-local behaviour worth promoting. **Checking the visible task book says otherwise.**

The v2.3 task book lists, as two independent bullets:

```
- 过滤：--filter 支持 field>N、field<N、field=V、field!=V，数值比较必须按数值语义
- 单位：--unit f 把 temp 从摄氏度精确转为华氏度（c * 9/5 + 32）
```

It **never states the interaction order**. The three hidden tests
(`d114_filter_before_unit_conversion`, `d6_unit_after_filter`,
`t4b_unit_f_applies_after_filter`) all require "filter compares Celsius; unit converts
after". All 6 model families implemented the other reading, or converted the threshold.

Same for `md_table_escaping` (p=0.06): the spec says "md：表格 + 统计行（mean 为算术平均）"
and never mentions escaping `|`.

**Both are under-specified.** Their between-model variance is zero, so they contribute
nothing to discrimination while costing score mass. They are precisely the failure mode
the brief's §11B warns about.

This also gives a clean, mechanical test for the V7 design:

> a behaviour whose hidden test requires a rule that appears **nowhere** in the visible
> contract is a spec gap, not a hard behaviour. Measured p <= 0.10 with zero between-model
> variance is the signature.

## 4. Repetition vs score mass — measured

81 legacy tests collapse to 24 semantic behaviours. The relationship between how many
tests a behaviour got and how often it actually failed:

**correlation(n_tests, fail_rate) = 0.130.**

| behaviour | tests | fail rate | score mass |
|---|---:|---:|---:|
| `ndjson_malformed_tolerance` | 7 | 0.78 | 5.44 |
| `filter_multi_and_ordering` | 5 | 0.94 | 4.72 |
| `cli_full_chain` | 6 | 0.75 | 4.50 |
| `md_table_escaping` | **1** | **0.94** | 0.94 |

Total live score mass: **24.6 of 81 tests**. Roughly 70% of the old suite is passed by
everyone and contributes nothing. The brief's §1.4 hypothesis (that the old raw score
amplified hard behaviours) **is not supported by the data** — repetition landed on
tolerance/plumbing, while the hardest item got one slot.

## 5. Proposed V7 structure (for Phase 6, not yet frozen)

| tier | contents | weight |
|---|---|---|
| **main score** | the 8 live behaviours | explicit per-behaviour weights, frozen and public |
| `basic` | `whitespace_trimming`, `cli_exit_codes`, `csv_dialect_robustness` | 1 |
| `inference` | `legacy_temperature_fallback`, `nonfinite_rejected`, `timestamp_microseconds_preserved`, `bool_is_not_numeric` | 2 |
| `hard` | `cli_full_chain` + the four unmeasured closure probes once piloted | 3 |
| **regression** | 10 ceiling + 4 noise | unscored |
| **observe-only** | `stop_decision_depth` | never scored |

Weighting is per the brief's §14: three fixed tiers, no black-box weighting, fixed before
freeze. **No behaviour is duplicated into multiple tests to buy weight** — the legacy
practice that produced 7 tests for one behaviour is explicitly not carried over.

## 6. Open decisions deferred to later phases

1. The four unmeasured closure probes need a pilot before they can be graded (Phase 4).
2. The two spec-gap behaviours need a decision: state the rule in the visible contract and
   re-measure, or drop them. They must not silently enter the main score.
3. `gemini-3.5-flash` is only partially usable (2 of 3 runs died mid-run), so the Phase-4
   calibration matrix should mark it as a weak row rather than drop it.
4. A holdout model set is still undefined (brief §12). With the current availability
   constraints the honest split is: calibrate on the six families measured here, and treat
   every future model as out-of-sample.

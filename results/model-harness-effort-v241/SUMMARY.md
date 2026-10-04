# space-bunny-free x dsv4-behavior-bench V5 **v2.4.1** (68 tests) - reasoning-effort sweep

One-shot, blind, n=5 per level (25 runs, none discarded). Graded host-side with the
frozen `grade_v5.py` after all frozen hashes and both calibration baselines verified.

## Results

| effort | V5 raw /68 per run | mean +/- sd | behavior | legacy /81 |
|---|---|---:|---:|---:|
| low | 63/67/68/68/67 | 66.60 +/- 2.07 | 0.958 | 79.4 |
| medium | 68/68/64/68/68 | 67.20 +/- 1.79 | 0.976 | 79.6 |
| high | 68/68/67/67/68 | 67.60 +/- 0.55 | 0.988 | 80.0 |
| xhigh | 68/68/68/67/68 | 67.80 +/- 0.45 | 0.994 | 80.0 |
| max | 68/68/68/68/68 | 68.00 +/- 0.00 | 1.000 | 80.0 |

Clean 68/68 runs: **18/25 (72%)**

Level means are strictly monotone in effort (low < medium < high < xhigh < max), and
the `max` level scored 68/68 in every replicate with behaviour 1.000.

## Errata effect (v2.4.0 -> v2.4.1)

| measure | v2.4.0 /66 | v2.4.1 /68 |
|---|---:|---:|
| clean full-score runs | 7/25 (28%) | **18/25 (72%)** |
| `test_i3_validation_before_dedupe` failures | 16/25 | **0/25** |
| runs emitting `temp:null` for non-finite input | 4/25 | **0/25** |
| new `a13`/`a14` failures | n/a | **0/25** |

## Failing tests across all 25 runs

| test | count |
|---|---:|
| `test_c7_malformed_filter_raises_value_error` | 4/25 |
| `test_a4_non_object_record_malformed` | 2/25 |
| `test_c1_default_on_error_is_skip` | 1/25 |
| `test_c2_skip_nonzero_skipped_still_exit0` | 1/25 |
| `test_a10_library_cli_agree` | 1/25 |
| `test_b10_library_cli_correspond` | 1/25 |
| `test_a3_fail_skip_duality_unparseable_ts` | 1/25 |
| `test_a12_skipped_not_double_counted` | 1/25 |
| `test_m8_transform_totals_conserved` | 1/25 |
| `test_c4_fail_cli_exit1` | 1/25 |

## Process metrics (mean per level)

| effort | steps | thinking events | tool calls |
|---|---:|---:|---:|
| low | 37 | 17 | 46 |
| medium | 37 | 17 | 46 |
| high | 61 | 24 | 68 |
| xhigh | 47 | 22 | 61 |
| max | 55 | 27 | 72 |

## Statistics

- Between-level permutation test (20k label shuffles, between-group SS): raw p = 1.000,
  behaviour p = 1.000. The between-level spread (1.40) stays inside the pooled
  within-level sd (1.26), so no level separates from any other.
- Trend test over all 25 runs (Spearman rho between effort rank and raw score):
  **rho = 0.399, permutation p = 0.051**. The direction is now consistent across all
  five levels - the first time that happened - but a 1.40-point effect is still too
  small to call at this sample size.

## Integrity audit (25/25 CLEAN)

| check | result |
|---|---|
| `tests/` + `tools/` sources byte-identical to the frozen seed | 25/25 |
| grading-suite / reference leakage hits | 0 |
| absolute paths outside the candidate's own workspace | 0 |

## Toolchain

- dsh 0.2.0-rc.2, profile `ef-dev`, Windows node
- model `space-bunny-free` via `opencode-zen`; `tool-web`, `tool-subagent`, `tool-subagent-fork` disabled
- grader `grade_v5.py`, Python 3.14.4 / pytest 9.0.2
- bench commit `b1d7006`; 26/26 frozen sha256 verified before scoring

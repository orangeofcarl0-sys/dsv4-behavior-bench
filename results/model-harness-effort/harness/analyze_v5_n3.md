# V5 effort sweep - aggregate over n=3 replicates

Per-run values in rep order. Mean +/- sample sd.

| effort | V5 raw per run | raw mean +/- sd | behavior per run | behavior mean | legacy per run | steps per run | wall per run |
|---|---|---:|---|---:|---|---|---|
| low | 65/65/66 | 65.3 +/- 0.6 | 0.969/0.969/1.000 | 0.979 | 80/80/80 | 32/39/35 | 202s/328s/601s |
| medium | 65/65/62 | 64.0 +/- 1.7 | 0.969/0.969/0.875 | 0.938 | 80/80/79 | 44/31/49 | 456s/414s/600s |
| high | 65/66/66 | 65.7 +/- 0.6 | 0.969/1.000/1.000 | 0.990 | 80/80/80 | 62/34/33 | 477s/417s/659s |
| xhigh | 64/65/66 | 65.0 +/- 1.0 | 0.938/0.969/1.000 | 0.969 | 79/80/80 | 72/62/50 | 1290s/840s/659s |
| max | 66/65/65 | 65.3 +/- 0.6 | 1.000/0.969/0.969 | 0.979 | 78/80/78 | 50/62/87 | 1290s/866s/798s |

## Failing tests per replicate

**low**
- rep1: `test_c7_malformed_filter_raises_value_error`
- rep2: `test_i3_validation_before_dedupe`
- rep3: none (66/66)

**medium**
- rep1: `test_i3_validation_before_dedupe`
- rep2: `test_i3_validation_before_dedupe`
- rep3: `test_c3_transform_fail_raises_data_error`, `test_c5_atomic_transform_output_absent_stays_absent`, `test_c7_malformed_filter_raises_value_error`, `test_a9_transform_fail_preserves_existing`

**high**
- rep1: `test_i3_validation_before_dedupe`
- rep2: none (66/66)
- rep3: none (66/66)

**xhigh**
- rep1: `test_c4_fail_cli_exit1`, `test_i3_validation_before_dedupe`
- rep2: `test_i3_validation_before_dedupe`
- rep3: none (66/66)

**max**
- rep1: none (66/66)
- rep2: `test_i3_validation_before_dedupe`
- rep3: `test_i3_validation_before_dedupe`

## Behaviour category means over replicates

| effort | contract | interaction | adversarial | boss | metamorphic |
|---|---:|---:|---:|---:|---:|
| low | 0.96 | 0.93 | 1.00 | 1.00 | 1.00 |
| medium | 0.88 | 0.87 | 0.94 | 1.00 | 1.00 |
| high | 1.00 | 0.93 | 1.00 | 1.00 | 1.00 |
| xhigh | 0.96 | 0.87 | 1.00 | 1.00 | 1.00 |
| max | 1.00 | 0.87 | 1.00 | 1.00 | 1.00 |


# V5 effort sweep - aggregate over n=5 replicates

Per-run values in rep order. Mean +/- sample sd.

| effort | V5 raw per run | raw mean +/- sd | behavior per run | behavior mean | legacy per run | steps per run | wall per run |
|---|---|---:|---|---:|---|---|---|
| low | 65/65/66/65/65 | 65.2 +/- 0.4 | 0.969/0.969/1.000/0.969/0.969 | 0.975 | 80/80/80/80/80 | 32/39/35/38/43 | 202s/328s/601s/335s/306s |
| medium | 65/65/62/66/63 | 64.2 +/- 1.6 | 0.969/0.969/0.875/1.000/0.906 | 0.944 | 80/80/79/80/79 | 44/31/49/39/53 | 456s/414s/600s/396s/523s |
| high | 65/66/66/65/65 | 65.4 +/- 0.5 | 0.969/1.000/1.000/0.969/0.969 | 0.981 | 80/80/80/80/80 | 62/34/33/57/51 | 477s/417s/659s/600s/589s |
| xhigh | 64/65/66/66/65 | 65.2 +/- 0.8 | 0.938/0.969/1.000/1.000/0.969 | 0.975 | 79/80/80/80/80 | 72/62/50/46/66 | 1290s/840s/659s/600s/1612s |
| max | 66/65/65/65/63 | 64.8 +/- 1.1 | 1.000/0.969/0.969/0.969/0.906 | 0.963 | 78/80/78/78/79 | 50/62/87/51/44 | 1290s/866s/798s/721s/1616s |

## Failing tests per replicate

**low**
- rep1: `test_c7_malformed_filter_raises_value_error`
- rep2: `test_i3_validation_before_dedupe`
- rep3: none (66/66)
- rep4: `test_i3_validation_before_dedupe`
- rep5: `test_i3_validation_before_dedupe`

**medium**
- rep1: `test_i3_validation_before_dedupe`
- rep2: `test_i3_validation_before_dedupe`
- rep3: `test_c3_transform_fail_raises_data_error`, `test_c5_atomic_transform_output_absent_stays_absent`, `test_c7_malformed_filter_raises_value_error`, `test_a9_transform_fail_preserves_existing`
- rep4: none (66/66)
- rep5: `test_c7_malformed_filter_raises_value_error`, `test_i3_validation_before_dedupe`, `test_i5_cli_full_chain`

**high**
- rep1: `test_i3_validation_before_dedupe`
- rep2: none (66/66)
- rep3: none (66/66)
- rep4: `test_i3_validation_before_dedupe`
- rep5: `test_i3_validation_before_dedupe`

**xhigh**
- rep1: `test_c4_fail_cli_exit1`, `test_i3_validation_before_dedupe`
- rep2: `test_i3_validation_before_dedupe`
- rep3: none (66/66)
- rep4: none (66/66)
- rep5: `test_i3_validation_before_dedupe`

**max**
- rep1: none (66/66)
- rep2: `test_i3_validation_before_dedupe`
- rep3: `test_i3_validation_before_dedupe`
- rep4: `test_i3_validation_before_dedupe`
- rep5: `test_i3_validation_before_dedupe`, `test_i5_cli_full_chain`, `test_b8_full_cli_chain`

## Behaviour category means over replicates

| effort | contract | interaction | adversarial | boss | metamorphic |
|---|---:|---:|---:|---:|---:|
| low | 0.97 | 0.88 | 1.00 | 1.00 | 1.00 |
| medium | 0.90 | 0.84 | 0.97 | 1.00 | 1.00 |
| high | 1.00 | 0.88 | 1.00 | 1.00 | 1.00 |
| xhigh | 0.97 | 0.88 | 1.00 | 1.00 | 1.00 |
| max | 1.00 | 0.80 | 1.00 | 0.97 | 1.00 |


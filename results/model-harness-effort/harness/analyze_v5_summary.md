# space-bunny-free x dsv4-behavior-bench **V5** (datapipe v2.4) - reasoning-effort sweep

One-shot, blind, n=1 per level. Graded host-side with the frozen `grade_v5.py`.

## Results

| effort | V5 raw /66 | behavior /32 | core | inter | adv | boss | meta | legacy /81 | public /25 | wall | steps | think | calls |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low | **65/66** | **0.969** (31/32) | 18 | 8 | 19 | 11 | 9 | 80/81 | 25/25 | 202s | 32 | 13 | 44 |
| medium | **65/66** | **0.969** (31/32) | 19 | 7 | 19 | 11 | 9 | 80/81 | 25/25 | 456s | 44 | 23 | 55 |
| high | **65/66** | **0.969** (31/32) | 19 | 7 | 19 | 11 | 9 | 80/81 | 25/25 | 477s | 62 | 28 | 78 |
| xhigh | **64/66** | **0.938** (30/32) | 18 | 7 | 19 | 11 | 9 | 79/81 | 25/25 | 1290s | 72 | 21 | 83 |
| max | **66/66** | **1.000** (32/32) | 19 | 8 | 19 | 11 | 9 | 78/81 | 25/25 | 1290s | 50 | 22 | 72 |

Calibration anchors (reproduced locally before scoring):

| object | V5 raw | behavior | legacy |
|---|---:|---:|---:|
| `v5ref` (v2.4 reference) | 66/66 | 1.000 | 80/81 |
| `gold2` (v2.3-complete solver, from README) | 35/66 | 0.469 | 81/81 |
| `gold` (v2.3 GOLD, from README) | 33/66 | 0.438 | 76/81 |
| `v5seed` (broken seed) | 17/66 | 0.094 | 37/81 |

## Category behaviour scores

| effort | contract | interaction | adversarial | boss | metamorphic |
|---|---:|---:|---:|---:|---:|
| low | 0.88 | 1.00 | 1.00 | 1.00 | 1.00 |
| medium | 1.00 | 0.80 | 1.00 | 1.00 | 1.00 |
| high | 1.00 | 0.80 | 1.00 | 1.00 | 1.00 |
| xhigh | 0.88 | 0.80 | 1.00 | 1.00 | 1.00 |
| max | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Failures and unsatisfied behaviours

**low** - 65/66 raw, 0.969 behaviour, 1 unsatisfied behaviour(s)
- failing test `v5/core/...::test_c7_malformed_filter_raises_value_error`
- unsatisfied behaviour `contract/usage_vs_data_error` (blocked by test_c7_malformed_filter_raises_value_error)

**medium** - 65/66 raw, 0.969 behaviour, 1 unsatisfied behaviour(s)
- failing test `v5/interaction/...::test_i3_validation_before_dedupe`
- unsatisfied behaviour `interaction/ordering_dedupe_filter_unit` (blocked by test_i3_validation_before_dedupe)

**high** - 65/66 raw, 0.969 behaviour, 1 unsatisfied behaviour(s)
- failing test `v5/interaction/...::test_i3_validation_before_dedupe`
- unsatisfied behaviour `interaction/ordering_dedupe_filter_unit` (blocked by test_i3_validation_before_dedupe)

**xhigh** - 64/66 raw, 0.938 behaviour, 2 unsatisfied behaviour(s)
- failing test `v5/core/...::test_c4_fail_cli_exit1`
- failing test `v5/interaction/...::test_i3_validation_before_dedupe`
- unsatisfied behaviour `contract/fail_cli_exit_one` (blocked by test_c4_fail_cli_exit1)
- unsatisfied behaviour `interaction/ordering_dedupe_filter_unit` (blocked by test_i3_validation_before_dedupe)

**max** - 66/66 raw, 1.000 behaviour, 0 unsatisfied behaviour(s)
- none - full pass, every behaviour satisfied

## Process metrics

| effort | steps | thinking events | tool calls | tool mix | wall |
|---|---:|---:|---:|---|---:|
| low | 32 | 13 | 44 | read 16 / bash 13 / write 8 / edit 6 / glob 1 | 202s |
| medium | 44 | 23 | 55 | bash 23 / read 13 / write 10 / edit 9 | 456s |
| high | 62 | 28 | 78 | bash 29 / read 26 / write 10 / edit 10 / todo_write 2 | 477s |
| xhigh | 72 | 21 | 83 | read 25 / edit 22 / bash 21 / write 12 / todo_write 3 | 1290s |
| max | 50 | 22 | 72 | read 21 / bash 20 / edit 19 / write 9 / todo_write 3 | 1290s |

## Integrity audit

| effort | tool calls | tests/ + tools/ source | grading-suite leak hits | absolute paths outside own workspace | verdict |
|---|---:|---|---:|---|---|
| low | 44 | unchanged | 0 | 0 | CLEAN |
| medium | 55 | unchanged | 0 | 0 | CLEAN |
| high | 78 | unchanged | 0 | 0 | CLEAN |
| xhigh | 83 | unchanged | 0 | 0 | CLEAN |
| max | 72 | unchanged | 0 | 0 | CLEAN |

All absolute paths a tool call touched were inside the candidate's own workspace or
system locations; `tests/` and `tools/` source files are byte-identical to the
frozen seed (`__pycache__` excluded - running the public tests regenerates bytecode).

## Toolchain

- dsh 0.2.0-rc.2, profile `ef-dev`, Windows node
- model `space-bunny-free` via `opencode-zen`; `tool-web`, `tool-subagent`, `tool-subagent-fork` disabled
- grader `grade_v5.py` on Python 3.14.4 / pytest 9.0.2; frozen hashes verified before the run

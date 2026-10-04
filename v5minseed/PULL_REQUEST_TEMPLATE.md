# datapipe 修复交付报告

## 初始诊断

（运行 `python3 tools/run_public_tests.py` 与 `python3 tools/run_debug_probe.py`，
记录初始结果、失败清单与定位。）

## 修改说明

（按 `ONBOARDING_TODO.md` 的 v2.4 规范逐项说明改动：`--on-error`、atomic
output、多 `--filter`、处理顺序。）

## 最终验证

（public 测试结果；并手工验证 `--on-error fail` 的 atomic output 与多个
`--filter` 的 AND 语义。）

## 未验证风险

（列出尚未覆盖、无法在本地验证的点。）

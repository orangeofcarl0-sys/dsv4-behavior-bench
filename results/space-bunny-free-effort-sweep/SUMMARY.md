# space-bunny-free × reasoning-effort 扫描（one-shot）

- 运行日期：2026-10-03
- 模型：`space-bunny-free`（OpenCode Zen）
- 思考强度：low / medium / high / xhigh / max（该模型不支持 off/none）
- 每档 n=1，one-shot，无重试、无多轮、无方差测量

## 协议

1. **seed**：datapipe v2.2.1 broken seed（git `61eff68`，tag `datapipe-v2-broken-seed`）。
   五份工作区为**逐字节**副本（tree md5 `6aca0e6fbaa1efe594c3708a6fc21c9e`，5/5 一致）。
2. **任务书**：只给工作区根目录的 `ONBOARDING_TODO.md`（v2.3 规格 + 必须流程 + 硬性约束）。
3. **盲测**：本套件与 gold/gold2 不在候选工作区内；候选的 web 工具与 subagent 工具被禁用。
4. **代理**：每档一个独立 headless 代理进程，配置 overlay 固定 provider/model 与 `reasoningEffort`，
   cwd 即候选工作区（overlay 见 `overlays/`）。
5. **评分**：宿主侧交付后统一执行（脚本见 `harness/grade.py`，等价于
   `DATAPIPE_REPO=<repo> python -m pytest d10 d11 d12 t2 t3 t4 v4 -q`），评分前未展示给任何候选。

## 基线复现（评分前校验）

| 对象 | 本次复现 | 套件公布值 | 一致 |
|---|---:|---:|:--:|
| seed（未修复） | 25/81（public 9/25） | 25/81（public 16 失败） | 是 |
| gold2（参考实现） | 81/81 | 81/81 | 是 |

## 结果

| 思考强度 | 总分/81 | public/25 | d10 | d11 | d12 | t2 | t3 | t4 | v4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low | 68 | 25 | 10 | 11 | 6 | 7 | 6 | 10 | 18 |
| medium | 63 | 25 | 11 | 10 | 7 | 7 | 6 | 7 | 15 |
| **high** | **78** | 25 | 10 | 11 | 8 | 8 | 6 | 11 | 24 |
| **xhigh** | **79** | 25 | 11 | 11 | 8 | 8 | 6 | 11 | 24 |
| max | 71 | 25 | 11 | 9 | 7 | 8 | 6 | 10 | 20 |

## 过程指标

| 强度 | steps | thinking 事件 | 工具调用 | 墙钟 | 工具构成 |
|---|---:|---:|---:|---:|---|
| low | 24 | 9 | 29 | 309s | bash 10 / read 7 / write 6 / edit 6 |
| medium | 27 | 12 | 33 | 382s | bash 13 / read 9 / edit 6 / write 5 |
| high | 32 | 12 | 43 | 1344s | read 17 / bash 15 / write 6 / edit 3 |
| xhigh | 43 | 19 | 58 | 650s | read 21 / bash 20 / write 9 / edit 6 |
| max | 45 | 20 | 58 | 722s | read 21 / bash 21 / write 8 / edit 4 |

思考强度越高，步数 / 思考事件 / 工具调用单调上升（24→45 步，9→20 个思考事件），
即 effort 参数确实生效。high 的 1344s 是重试退避造成的离群值，不是工作量信号。

## 残留失败

- **low（13）**：集中于 NDJSON 坏行容错（d12/t2/t4/v4 共 6 项）、legacy `temperature` 回退（d3）、
  md 表格竖线转义、filter 缺字段、微秒保留。
- **medium（18）**：同上，另加 extless JSON 嗅探（t4a/d4）与 `unit_f_applies_after_filter` /
  `d6_unit_after_filter` 的算子顺序。
- **high（3）**：`d102_microseconds_preserved`、`d122_emit_skips_malformed_line`、
  `d127_cli_transform_malformed_exit1`。
- **xhigh（2）**：`d126_md_table_pipe_escaped`、`d127_cli_transform_malformed_exit1`。
- **max（10）**：NaN/Inf 拒绝（d112/d113）、时间戳空白裁剪（d2）、legacy temperature（d3）、
  d127 退出码，以及 d12/t4 的坏行与转义。

逐条清单见 `grades/grade_<level>.json` 的 `failures` 字段。

## 完整性审计

- 五份产出均**未**修改 `tests/` 与 `tools/`（满足 ONBOARDING_TODO.md 硬性约束）。
- 五个代理的事件流中**零**命中评分套件路径（`ablation-eval` / 本套件名 / `grade_v3` /
  `gold/` / seed 源目录）——盲测成立，无泄露。
- 相对 seed，修改面集中在 `datapipe/{ingest,transform,emit,cli}.py`；xhigh 额外拆出
  `normalize.py`/`records.py`，max 拆出 `values.py`（模块边界保持良好）。
- public 层 5/5 全部 25/25 —— 与套件结论一致：公开测试对模型差异完全不敏感，
  区分度完全落在 d12 / t4 / v4。

## 结论

1. **强度有用但非单调**：high(78) / xhigh(79) 明显优于 low(68) / medium(63)，
   但 max(71) 反而低于 high 与 xhigh。
2. **甜点区在 high–xhigh**：两档都拿到 v4 24/24 全绿，与 GOLD 的差距只剩 2–3 项，
   全部落在 d12 的对抗边界（md 竖线转义、transform 坏行退出码）。
3. **不能过度解读**：n=1、无方差测量。medium(63) < low(68)、max(71) < high(78) 的非单调
   说明单次运行方差至少在 ±5–8 分量级；档位内部排序不可信，可靠曲线需 n≥3。

## 目录

```
run_metadata.json      运行元数据（协议、seed、逐档分数与过程指标）
grades/grade_<lv>.json 逐档逐套件分数与失败清单
overlays/effort_<lv>.yml  各档模型/思考强度 overlay（含禁用 web+subagent 的盲测设置）
harness/               评分脚本、运行脚本、任务书、事件流统计脚本
```

> 本目录内容已脱敏：本机绝对路径与用户名替换为 `<harness>` / `<workspace-root>` /
> `<seed-root>` / `<appdata>` / `<user>` 占位符，评分数据未作任何改动。

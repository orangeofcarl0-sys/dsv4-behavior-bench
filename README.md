# ablation-eval-v3

[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![dsh](https://img.shields.io/badge/dsh-0.1.0--rc.6-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-81-green)]()

> **V5 (datapipe v2.4) added 2026-10-04.** The legacy 81-test suite remains frozen
> and unchanged below. V5 adds a harder, behavior-scored layer on top: see
> [V5：datapipe v2.4 升级](#v5datapipe-v24-升级2026-10-04) at the end of this file.

轻量、零依赖的 **DeepSeek V4 行为区分度分级套件**：81 个纯 pytest 测试，
专门用于检验基于 dsv4 的 Harness / Agent 相关工作（persona 路由、工具面
收窄、思维模式预设）的真实效果差异。

## 实测对照：模型 one-shot 跑分

协议：同一份 seed（datapipe 2.2.1 重建版）的逐字节副本作为起点；每个候选在**盲测**下单轮修复
（只给 `ONBOARDING_TODO.md` 的 v2.3 规格，不可见 81 项套件），交付后由宿主侧统一评分：

```bash
DATAPIPE_REPO=<候选仓库根> python3 -m pytest d10 d11 d12 t2 t3 t4 v4 -q
```

| 候选 | 总分/81 | public/25 | d10 | d11 | d12 | t2 | t3 | t4 | v4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.6-sol | 81 | 25 | 11 | 11 | 10 | 8 | 6 | 11 | 24 |
| **space-bunny-free（effort=xhigh）** | **79** | 25 | 11 | 11 | 8 | 8 | 6 | 11 | 24 |
| **space-bunny-free（effort=high）** | **78** | 25 | 10 | 11 | 8 | 8 | 6 | 11 | 24 |
| m1-router（m1 路由预设） | 76 | 25 | 11 | 11 | 5 | 8 | 6 | 11 | 24 |
| **glm-5.3-flash** | **75** | 25 | 11 | 9 | 9 | 8 | 6 | 10 | 22 |
| **opencode-go / omen-alpha** | **71** | 25 | 11 | 11 | 9 | 7 | 6 | 9 | 18 |
| **deepseek-v4.1-flash-expires-on-0910** | **71** | 25 | 10 | 11 | 10 | 7 | 6 | 9 | 18 |
| **space-bunny-free（effort=max）** | **71** | 25 | 11 | 9 | 7 | 8 | 6 | 10 | 20 |
| **space-bunny-free（effort=low）** | **68** | 25 | 10 | 11 | 6 | 7 | 6 | 10 | 18 |
| deepseek-v4-flash | 66 | 25 | 11 | 11 | 10 | 7 | 6 | 8 | 13 |
| **space-bunny-free（effort=medium）** | **63** | 25 | 11 | 10 | 7 | 7 | 6 | 7 | 15 |
| deepseek-v4-flash-vision-exp | 65 | 25 | 11 | 10 | 10 | 7 | 6 | 8 | 13 |

- **public 全部 25/25**：公开测试对模型差异完全不敏感——这正是本套件存在的理由。
- **分离器是 d12 与 v4**：m1-router 的 d12 仅 5/10（对抗健壮性退化），模型候选 9-10/10；
  但 m1-router 的 v4 为 24/24，模型候选只有 18/24。
- omen-alpha 与 v4.1-flash 总分相同（71），10 项失败中 9 项重叠（legacy temperature 映射、
  NDJSON 坏行 skipped 计数、BOM 等规格外推断边界）；唯一分离点是 d12
  `test_d127_cli_transform_malformed_exit1`（omen-alpha 把坏行按跳过计数、退出 0）与
  d10 `test_d104_filter_whitespace_padded`（v4.1-flash 失败）。
- **glm-5.3-flash（75/81）是 GLM/omni 路线里的最高分**：t2 满分 8/8、v4 22/24；失败集中在 d11 的 NaN/Inf 拒绝、
  d12 的 transform 坏行退出码、以及 legacy temperature 回退。
- **space-bunny-free（effort=xhigh，79/81）是模型候选里的最高分**：v4 24/24 全绿、
  t2 满分 8/8、t4 11/11，仅 d12 停在 8/10；与 GOLD 的差距只剩 2 项，全部落在 d12 的对抗边界
  （md 表格竖线转义、transform 坏行退出码 1）。
- 运行日期：v4-flash / v4-flash-vision-exp 为 2026-08-21；omen-alpha / v4.1-flash-expires-on-0910 与 glm-5.3-flash 为 2026-09-09；
  space-bunny-free effort 扫描为 2026-10-03。
  每候选仅一轮（one-shot），未做方差测量，1-2 分差距应视为噪声级。

## 附加实验：reasoning-effort 扫描（space-bunny-free，2026-10-03）

同一个模型（`space-bunny-free`，OpenCode Zen）在本套件上跑满全部 5 档 `reasoning_effort`
（low / medium / high / xhigh / max；该模型不支持 off/none），协议与上表完全一致：盲测、one-shot、
n=1、逐字节 seed 副本、交付后宿主侧统一评分。

| effort | 总分/81 | public | d10 | d11 | d12 | t2 | t3 | t4 | v4 | steps | thinking | 工具调用 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low | 68 | 25 | 10 | 11 | 6 | 7 | 6 | 10 | 18 | 24 | 9 | 29 |
| medium | 63 | 25 | 11 | 10 | 7 | 7 | 6 | 7 | 15 | 27 | 12 | 33 |
| high | 78 | 25 | 10 | 11 | 8 | 8 | 6 | 11 | 24 | 32 | 12 | 43 |
| xhigh | 79 | 25 | 11 | 11 | 8 | 8 | 6 | 11 | 24 | 43 | 19 | 58 |
| max | 71 | 25 | 11 | 9 | 7 | 8 | 6 | 10 | 20 | 45 | 20 | 58 |

- **effort 参数确实生效**：步数 24→45、思考事件 9→20、工具调用 29→58 随强度单调上升，
  所以分数回落不是参数没传进去。
- **强度有用但非单调**：high(78) / xhigh(79) 明显优于 low(68) / medium(63)，
  但 max(71) 反而低于 high 与 xhigh。
- **甜点区在 high–xhigh**：两档都拿到 v4 24/24 全绿，距 GOLD 只剩 2 项，
  全部落在 d12 的对抗边界（md 表格竖线转义、transform 坏行退出码）。
- **档内排序不可信**：n=1、无方差测量。medium < low、max < high 的非单调说明
  单次方差至少在 ±5–8 分量级，比上表所说"1–2 分为噪声"更大；可靠曲线需 n≥3。
- public 层 5/5 全部 25/25 —— 再次印证本套件的核心论点：区分度完全落在 d12 / t4 / v4。

证据（逐档逐套件分数与失败清单、各档配置 overlay、评分与运行脚本、运行元数据）见
[`results/space-bunny-free-effort-sweep/`](results/space-bunny-free-effort-sweep/)，
汇总见其 [SUMMARY.md](results/space-bunny-free-effort-sweep/SUMMARY.md)。
该目录已脱敏（本机绝对路径与用户名替换为占位符），评分数据未作任何改动。

## 问题

标准评测（public/heldout）对 dsv4 的**行为差异不敏感**：在我们的消融矩阵中
（54+ 格，deepseek-v4-pro / v4-flash，persona × 工具面 × 路由 × 引导全谱系），
所有格 public/heldout 全部满分（25/25 + 8/8）——预设之间的真实机制差异
（we/let-me 轨迹、persona 带、工具目录）在分数上**完全不可见**：

| 评分层 | seed（未修复） | 全部消融格 | GOLD（修复版） |
|---|---|---|---|
| public (25) | 16 失败 | **全绿** | 全绿 |
| heldout (8) | 4 失败 | **全绿** | 全绿 |
| **区分度** | — | **0（饱和）** | — |

## 方案

把 dsv4 行为差异压进分数：7 个预校准套件（V1-V4 分级方法论迭代产物），
全部为**零依赖 pytest**，conftest 自动解析候选仓库：

| 套件 | 测试数 | 考察点 |
|---|---|---|
| d10 / d11 | 22 | 常规边界 + 规格推导（时区/微秒/负值/幂等/CLI 链） |
| d12 | 10 | 对抗性健壮性（坏行容错、bool 陷阱、数组输入、md 转义、退出码） |
| t2 / t3 / t4 | 25 | 分级能力 + 规格缺失推断（MIXED 族） |
| v4 | 24 | V4 核心区分（v4core 规格完整性 8 + 全量 16） |
| gold / gold2 | — | GOLD 参考实现（gold2 = 修复版全过） |

实测区分度（dsv4-pro 消融产物，2026-08-16）：

| 候选 | 分级总分 / 81 | d12 | t4 | v4 |
|---|---:|---:|---:|---:|
| **GOLD2**（修复版） | **81** | 10/10 | 11/11 | 24/24 |
| GOLD / m1-router | 76 | 5/10 | 11/11 | 24/24 |
| anchored 系 | 64-66 | 6/10 | 9/11 | 14-16/24 |
| router 系（m2/m4/m5/m6） | 62 | 4-5/10 | 9/11 | 13-14/24 |
| **seed**（未修复基线） | **25** | 5/10 | 2/11 | 4/24 |

同一个 dsv4 模型、同一任务、同一批产物——**61 分跨度**，且与轨迹指纹
（we/let-me 密度）方向一致：能区分"persona 是否生效、工具面收窄是否
带来质量回归、路由/引导是否真实改变产出"。

## 轻量

- **零依赖**：纯 pytest + 标准库，conftest 自解析 `DATAPIPE_REPO`，无框架、无安装
- **快**：单候选全套 81 测试 < 10 秒（含 gold 对照 < 30 秒）
- **一行运行**：

```bash
DATAPIPE_REPO=<候选仓库根> python3 -m pytest d10 d11 d12 t2 t3 t4 v4 -q
```

或 PowerShell 一键评分（含 public/heldout 对照）：

```powershell
powershell -File grade_v3.ps1 -Repo <候选仓库根> -Label <名字>
```

## 适用场景

- **DSH 预设消融**：persona（spec/react/weak）、首轮工具面收窄、任务路由、
  引导注入的机制检验——轨迹指标说"变没变"，本套件说"好不好"
- **基于 dsv4 的 agent 工程**：prompt/persona 迭代的回归防线（public 全绿
  掩盖的退化在 d12/t4/v4 上现形）
- **harness 层改动验收**：工具 schema、注入上下文、模型路由配置的批量对比

## 验证

- 校准门槛（V1-V4 方法论）：GOLD ≥ 8/10 且弱基线 ≤ 5/10，逐测试可归因
- GOLD2 81/81 全绿无回归（v4 24/24、d10 11/11、d11 11/11、d12 10/10、t2 8/8、
  t3 6/6、t4 11/11）
- seed 25/81：套件对未修复基线不虚报

## 局限

- datapipe 任务专用（Python 遥测数据管道 CLI）；2048 等任务的同类分级套件待建
- t2/t4 存在规格推断主观性：校准以 GOLD 对照 + 逐测试归因为准
- 评分目标产物为"修复型任务"产出；构建型（greenfield）任务建议另行校准

## License

MIT。套件源于 DeepSeek Harness 消融实验方法论（V1-V4 分级迭代）。

---

# V5：datapipe v2.4 升级（2026-10-04）

上面 81 项套件已冻结、不改动。V5 在同一 datapipe 修复任务上新增一层更难的
**语义行为评分**，目标是在保持「轻量 Flash 快评」定位的前提下打破 75–79/81
的顶部饱和。

- **新增 contract（少而深）**：`--on-error skip|fail`（默认 skip）、`fail` 下的
  **atomic output**（失败不留 partial、已有文件不被 truncate）、重复
  `--filter` 的 **AND 语义**；并冻结处理顺序
  `normalize → validation → dedupe → filter(s) → unit → emit`。
  不引入 SQL/表达式语言、async、数据库、插件框架、第三方依赖。
- **测试 66 项**，按语义分层：`v5/core` 19、`v5/interaction` 8、
  `v5/adversarial` 19、`v5/boss` 11、`v5/metamorphic` 9。
  新增测试以**组合语义**为主（一个 case 同时压 3–7 个 contract），
  metamorphic 用固定 seed 的 stdlib 生成器测不变量。
- **行为评分取代纯计数**：`v5/behavior_manifest.json` 把 32 个 behavior 映射到
  测试；behavior 只有在**其全部测试通过**时才算满足，overall = 五类均值的
  透明加权。彻底消除「一个 malformed-NDJSON 缺陷重复扣很多分」。
- **frozen artifact 进仓库**：`spec/ONBOARDING_TODO_v2.4.md`（candidate 任务书，
  逐字节复制进候选工作区）、`spec/V5_DESIGN.md`（设计依据 + provenance）、
  `spec/FROZEN_HASHES.txt`。
- **V5 reference 与 broken seed 都在仓库内**：`v5ref/`（76→ 全绿）、
  `v5seed/`（低分基线）。

## 运行

```bash
python grade_v5.py <候选仓库根> --label <名字> --json out.json
```

输出 machine-readable JSON，含每个套件固定 expected 数（collection/import error
标记 suite invalid 并按失败计，denominator 不缩小）、raw `passed/total`、
core/interaction/adversarial/boss/metamorphic 分项与 overall behavior score、
legacy 81 套件（单独报告，保证历史可比）。

验证（本机 Python 3.11 / pytest 9.1）：

| 对象 | V5 raw | behavior | legacy/81 | runtime |
|---|---:|---:|---:|---:|
| `v5ref`（v2.4 reference） | 66/66 | 1.000 | 80/81（仅 d127 有意 supersede） | ~20s |
| `gold2`（v2.3 完成版） | 35/66 | 0.469 | 81/81 | — |
| `gold`（v2.3 GOLD） | 33/66 | 0.438 | 76/81 | — |
| `v5seed`（broken baseline） | 17/66 | 0.094 | 37/81 | ~19s |

mutation sanity：`python mutation_check.py` 对 reference 施加 8 类单点 mutation
（only-last-filter / filter-after-unit / fail→skip / partial-output /
`temp or temperature` / broad-except / dedupe-keep-first / skip→exit1），
**8/8 全部被捕获**（详见 `results/v5_mutation_check.json`）。

设计与 provenance 见 [`spec/V5_DESIGN.md`](spec/V5_DESIGN.md)，
leaderboard 运行须在 frozen suite 之后另行开展。

## 局限（V5）

- V5 与旧 81 套件的关系：legacy 保持冻结、单独报告；`transform` 的
  skip→exit0 是 v2.4 的有意演进，会与 legacy `d12::test_d127` 冲突，已在
  `spec/V5_DESIGN.md` 记录，不改 legacy。
- `--on-error` 默认值、`DataError` 不继承 `ValueError` 属 **policy choice**，
  已在 spec 写明。
- V5 对真实 Flash 模型的区分度尚未实测：当前只用 gold/gold2 作为梯度参照；
  正式 leaderboard 需在冻结后跑真实 candidate。


# ablation-eval-v3

[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![dsh](https://img.shields.io/badge/dsh-0.1.0--rc.6-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![V5](https://img.shields.io/badge/V5%20tests-66-green)]()
[![legacy](https://img.shields.io/badge/legacy%20tests-81-lightgrey)]()

轻量、零依赖的 **DeepSeek V4 行为区分度分级套件**：用一个小型 datapipe 修复任务，
把基于 dsv4 的 Harness / Agent 工作的真实效果差异压进分数。

- **当前基准：V5（datapipe v2.4）** — 66 项组合语义测试 + 行为评分，见下。
- **遗产基准：V1–V4（datapipe v2.3，81 项）** — 已冻结、结果已遗产化，见文末。

---

# 当前基准：V5 / datapipe v2.4

> **⚠️ 旧 81 分结果已遗产化（superseded），与 V5 不可比。**
> 它们跑在 **v2.3 规格 + 旧 broken seed** 上，分母、任务书、seed 全部不同；
> 顶部也已饱和（强 Flash 已达 75–79/81）。
> 切换 V5 后 **所有候选必须全面重测**：同一盲测/one-shot 协议，改用
> `spec/ONBOARDING_TODO_v2.4.md` + `v5seed`，宿主侧 `grade_v5.py` 评分。
> 旧分数仅作历史留档，不得与 V5 分数并列。

## 为什么升级

旧套件把“单点边界 → 局部修复”做到了极致，强模型已接近满分，且一个缺陷常被多个
测试重复覆盖（malformed-NDJSON 一项分散在 t2/t4a/v4/v4core 共 5+ 处），raw `/81`
带有隐式重复加权。V5 把难度轴从「更多单点边界」换成：

> **少量新增 contract × 非局部组合 × 一致性 × 错误策略 × atomicity。**

## 新增 contract（少而深）

- `--on-error skip|fail`（默认 `skip`），CLI + library 等价语义；`DataError`
  与 `ValueError` 可区分（数据错误 vs 用法错误）。
- `fail` 下的 **atomic output**：失败不留 partial，已有文件不被 truncate。
- 重复 `--filter` 的 **AND 语义**；冻结处理顺序
  `normalize → validation → dedupe → filter(s) → unit → emit`。
- 唯一有意行为变更：`skip` 时退出码为 **0**（supersede 旧的 skip→exit1）。

不引入 SQL/表达式语言、async、数据库、插件框架、第三方依赖、LLM judge。

## 测试结构（66 项）

| 套件 | 测试数 | 考察点 |
|---|---:|---|
| `v5/core` | 19 | v2.4 明确 contract（错误策略、atomicity、AND、顺序、退出码） |
| `v5/interaction` | 8 | 跨模块一致性、算子顺序、多约束组合 |
| `v5/adversarial` | 19 | 错误分类、坏输入、atomicity、表示边界 |
| `v5/boss` | 11 | 高信息密度端到端 composite（B1–B11） |
| `v5/metamorphic` | 9 | 固定 seed 确定性不变量（幂等 / 表示不变 / 顺序不变 / 守恒） |

新增测试以**组合语义**为主：一个 case 同时压 3–7 个 contract，要求完整 pipeline
心智模型，而不是作者知道答案的冷门 corner case。

## 行为评分（取代纯计数）

`v5/behavior_manifest.json` 把 **32 个 behavior → 测试**；behavior 只有在**其全部
测试通过**时才算满足，类别分 = 满足数 / 该类别 behavior 数，overall = 五类均值。
同一行为被多个测试覆盖不会获得额外权重——彻底消除「一个 malformed-NDJSON 缺陷
重复扣很多分」。每个 behavior 标注 provenance（`explicit-v2.4-contract` /
`backward-compatibility` / `cross-module-invariant` / `robustness-policy`）。

## 运行

```bash
python grade_v5.py <候选仓库根> --label <名字> --json out.json
```

输出 machine-readable JSON：每个套件固定 expected 数（collection/import error 标记
suite invalid 并按失败计，**denominator 不缩小**）、raw `passed/total`、
core/interaction/adversarial/boss/metamorphic 分项与 overall behavior score，
以及 legacy 81 套件（单独报告，仅保证历史可比）。

## 校准（本机 Python 3.11 / pytest 9.1）

| 对象 | V5 raw | behavior | legacy/81 | runtime |
|---|---:|---:|---:|---:|
| `v5ref`（v2.4 reference） | 66/66 | **1.000** | 80/81（仅 d127 有意 supersede） | ~17–20s |
| `gold2`（v2.3 完成版，作为“代理能力”参照） | 35/66 | 0.469 | 81/81 | — |
| `gold`（v2.3 GOLD） | 33/66 | 0.438 | 76/81 | — |
| `v5seed`（broken baseline） | 17/66 | **0.094** | 37/81 | ~19s |
| 语法错误注入（collection error） | 0/66 | 0.000 | 0/81 | — |

mutation sanity：`python mutation_check.py` 对 reference 施加 8 类单点 mutation
（only-last-filter / filter-after-unit / fail→skip / partial-output /
`temp or temperature` / broad-except / dedupe-keep-first / skip→exit1），
**8/8 全部被捕获**（详见 `results/v5_mutation_check.json`）。

**注意**：表中只有 reference / seed / 旧 GOLD 的校准值。
首个真实模型 V5 跑分见下方 leaderboard（`space-bunny-free`，2026-10-04，n=5）。
其余候选仍须用 v2.4 任务书 + `v5seed` 重测后方可入榜。

### V5 leaderboard

| 候选 | V5 raw /66 | behavior | legacy /81 | n | 日期 |
|---|---:|---:|---:|---:|---|
| `space-bunny-free`（reasoning-effort 扫描，5 档均值） | **65.4** | **0.981** | 80.0 | 5 | 2026-10-04 |
| `space-bunny-free` @ high（单次最佳档） | 65.40 ± 0.55 | 0.981 | 80.0 | 5 | 2026-10-04 |
| `v5ref`（v2.4 reference，非候选） | 66 | 1.000 | 80 | — | — |
| `v5seed`（broken baseline，非候选） | 17 | 0.094 | 37 | — | — |

> 旧榜分数（见下文遗产区）**不可**迁入此表。切换 benchmark 后所有候选必须全面重测。
> 本表首行为 5 档 reasoning-effort 的均值，**不是**某一档的单次成绩。

## 附加实验：reasoning-effort 扫描（space-bunny-free，V5，n=5）

同一模型跑满全部 5 档 `reasoning_effort`，协议与历史完全一致：盲测、one-shot、
逐字节 `v5seed` 副本、交付后宿主侧 `grade_v5.py` 统一评分。
**每档 n=5（25 次运行，0 次被剔除）**——与上方所有 one-shot 行不同，本节是重复测量。

| effort | V5 raw /66 逐轮 | 均值 ± sd | behavior | legacy /81 | wall |
|---|---|---:|---:|---:|---|
| low | 65 / 65 / 66 / 65 / 65 | 65.20 ± 0.45 | 0.975 | 80.0 | 202–601s |
| medium | 65 / 65 / 62 / 66 / 63 | **64.20 ± 1.64** | 0.944 | 79.6 | 396–600s |
| high | 65 / 66 / 66 / 65 / 65 | **65.40 ± 0.55** | **0.981** | 80.0 | 417–659s |
| xhigh | 64 / 65 / 66 / 66 / 65 | 65.20 ± 0.84 | 0.975 | 79.8 | 600–1612s |
| max | 66 / 65 / 65 / 65 / 63 | 64.80 ± 1.10 | 0.963 | **78.6** | 721–1616s |

- **effort 对 V5 分数无可检测影响**：置换检验（2 万次标签重排，组间平方和）
  raw **p = 1.000**、behavior **p = 1.000**。组间均值跨度 1.20 分 ≈ 合并组内 sd 1.02。
  排序还会随 n 洗牌（`max` 在 n=3 并列最高，n=5 降到 64.80）。
- **顶部饱和**：均值区间 64.2–65.4 / 66，仅 7/25 次跑出干净 66/66。
  本模型远高于设计文档预期的 50–80% raw band——**v2.4 任务书把 contract 写得过死**，
  几乎没有留给模型推断的空间。
- **方差几乎全部来自一个测试**：`test_i3_validation_before_dedupe` 单独占
  **16/25** 次失败，且五档分布几乎均匀（3/3/3/3/4），与 effort 无关。
- **`max` 在 legacy 上稳定落后**（78.6，5 次里 4 次 78–79）：见下条。
- **V5 漏检非有限值**：`v5/*/test_*.py` 对 `nan`/`inf` 的字面覆盖为 **0 处**，
  v2.4 任务书也从未提及非有限值。25 次中有 4 次把 `temp:"nan"` 归一为 `temp: null`
  并写入输出（`max` 3/5、`xhigh` 1/5），而这些运行的 V5 分数是 64–66。
  **这意味着 V5 并未覆盖 legacy 81 项的全部语义**；若要替代 legacy，
  建议在任务书第 10 节补回非有限值要求并在 `v5/adversarial` 增加用例。

证据（25 次运行的逐档逐轮分数、行为明细、失败清单、5 档 overlay、
运行与评分脚本、完整性审计）见
[`results/model-harness-effort/`](results/model-harness-effort/)。
该目录已脱敏（本机绝对路径与用户名替换为占位符），评分数据未作任何改动。

## 仓库内 frozen artifact

| 路径 | 内容 |
|---|---|
| `spec/ONBOARDING_TODO_v2.4.md` | candidate 任务书（逐字节复制进候选工作区） |
| `spec/V5_DESIGN.md` | 设计依据、provenance、校准、风险、开发记录 |
| `spec/FROZEN_HASHES.txt` | spec / tests / reference / seed / grader 的 sha256 |
| `v5ref/` | v2.4 reference 实现（全绿） |
| `v5seed/` | plausible-but-wrong broken seed（低分基线） |
| `v5/behavior_manifest.json` | behavior → tests 映射与评分方法 |
| `grade_v5.py` / `mutation_check.py` | 评分器 / mutation 审计 |

## 局限（V5）

- `--on-error` 默认值、`DataError` 不继承 `ValueError` 属 **policy choice**，已写入 spec。
- `skip → exit 0` 与 legacy `d12::test_d127` 冲突，是 v2.4 有意演进，legacy 保持冻结。
- V5 对真实 Flash 模型的区分度**尚未实测**；需正式 candidate runs 才能验证。

---

# 遗产基准：V1–V4 / datapipe v2.3（81 项，已冻结）

> **状态：legacy / superseded。** 保留用于历史留档与回归对照，**不再作为主榜**。
> 所有下列分数都跑在 v2.3 规格与旧 seed 上，与 V5 不可比。目录 `d10/d11/d12/
> t2/t3/t4/v4` 与 `gold/gold2` 自 V5 起不再改动。
> 结果遗产化的完整说明见 [`results/LEGACY.md`](results/LEGACY.md)：
> 分母、任务书、起始 seed 全部不同，旧分数**不能**用于推断 V5 表现，也不能迁入 V5 榜。

## 旧 leaderboard：模型 one-shot 跑分（历史留档）

协议：同一份 seed（datapipe v2.2.1 重建版）的逐字节副本作为起点；每个候选在**盲测**下单轮修复
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

## 旧附加实验：reasoning-effort 扫描（space-bunny-free，2026-10-03）

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

## 旧套件方法论（V1–V4 迭代留档）

### 问题

标准评测（public/heldout）对 dsv4 的**行为差异不敏感**：在消融矩阵中
（54+ 格，deepseek-v4-pro / v4-flash，persona × 工具面 × 路由 × 引导全谱系），
所有格 public/heldout 全部满分（25/25 + 8/8）——预设之间的真实机制差异
（we/let-me 轨迹、persona 带、工具目录）在分数上**完全不可见**：

| 评分层 | seed（未修复） | 全部消融格 | GOLD（修复版） |
|---|---|---|---|
| public (25) | 16 失败 | **全绿** | 全绿 |
| heldout (8) | 4 失败 | **全绿** | 全绿 |
| **区分度** | — | **0（饱和）** | — |

### 方案

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

### 轻量

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

### 适用场景

- **DSH 预设消融**：persona（spec/react/weak）、首轮工具面收窄、任务路由、
  引导注入的机制检验——轨迹指标说"变没变"，本套件说"好不好"
- **基于 dsv4 的 agent 工程**：prompt/persona 迭代的回归防线（public 全绿
  掩盖的退化在 d12/t4/v4 上现形）
- **harness 层改动验收**：工具 schema、注入上下文、模型路由配置的批量对比

### 验证

- 校准门槛（V1-V4 方法论）：GOLD ≥ 8/10 且弱基线 ≤ 5/10，逐测试可归因
- GOLD2 81/81 全绿无回归（v4 24/24、d10 11/11、d11 11/11、d12 10/10、t2 8/8、
  t3 6/6、t4 11/11）
- seed 25/81：套件对未修复基线不虚报

### 局限（legacy）

- datapipe 任务专用（Python 遥测数据管道 CLI）；2048 等任务的同类分级套件待建
- t2/t4 存在规格推断主观性：校准以 GOLD 对照 + 逐测试归因为准
- 评分目标产物为"修复型任务"产出；构建型（greenfield）任务建议另行校准
- **顶部饱和**：强 Flash 已达 75–79/81，这是 V5 升级的直接动因

## License

MIT。套件源于 DeepSeek Harness 消融实验方法论（V1–V5 分级迭代）。

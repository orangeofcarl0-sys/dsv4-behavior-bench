# ablation-eval-v3

[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![dsh](https://img.shields.io/badge/dsh-0.1.0--rc.6-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![V5](https://img.shields.io/badge/V5%20tests-68-green)]()
[![legacy](https://img.shields.io/badge/legacy%20tests-81-lightgrey)]()

轻量、零依赖的 **DeepSeek V4 行为区分度分级套件**：用一个小型 datapipe 修复任务，
把基于 dsv4 的 Harness / Agent 工作的真实效果差异压进分数。

- **当前基准：V5（datapipe v2.4.1）** — 68 项组合语义测试 + 行为评分，见下。
- **实验：V5-Minimal（信息消融）** — 同 seed / 同 hidden / 同 grader，只换任务书与
  证据分布。**结果：仍饱和（9/9 满分）**，见下。
- **原型：V6（多任务 inference tier）** — ledger / framecodec / cfgmerge 三个
  微型 repo，短 issue + 固定工作预算。prototype + pilot，未 freeze。
- **遗产套件：V1–V4（datapipe v2.3，81 项）** — 测试套件保留冻结，结果、参考基线与
  旧评分器已移除，见文末。
- **校准 tier：V7（datapipe v2.3 + 两处规格修补）** — 由**真实 Flash population
  实测反选出的 5 个行为**构成主分，权重显式。**未 freeze**：两个强 family 打平。

> **三层定位**：V5 = compliance tier（饱和，不再扩张）；V6 = inference prototype
> （未定型）；**V7 = calibrated discrimination tier**（由 item 区分度反选，不是覆盖度驱动）。

---

# 当前基准：V5 / datapipe v2.4

> **⚠️ 旧 81 分结果与其参考基线（`gold/`、`gold2/`）已全部清理，与 V5 不可比。**
> 它们跑在 **v2.3 规格 + 旧 broken seed** 上，分母、任务书、seed 全部不同；
> 顶部也已饱和（强 Flash 已达 75–79/81）。
> 切换 V5 后 **所有候选必须全面重测**：同一盲测/one-shot 协议，改用
> `spec/ONBOARDING_TODO_v2.4.md` + `v5seed`，宿主侧 `grade_v5.py` 评分。
> 需要旧结果或旧基线时，从 git 历史取回（V5 之前的最后提交 `aa2d0a8`）。

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

## 测试结构（68 项）

| 套件 | 测试数 | 考察点 |
|---|---:|---|
| `v5/core` | 19 | v2.4 明确 contract（错误策略、atomicity、AND、顺序、退出码） |
| `v5/interaction` | 8 | 跨模块一致性、算子顺序、多约束组合 |
| `v5/adversarial` | 21 | 错误分类、坏输入、atomicity、表示边界、非有限值 |
| `v5/boss` | 11 | 高信息密度端到端 composite（B1–B11） |
| `v5/metamorphic` | 9 | 固定 seed 确定性不变量（幂等 / 表示不变 / 顺序不变 / 守恒） |

新增测试以**组合语义**为主：一个 case 同时压 3–7 个 contract，要求完整 pipeline
心智模型，而不是作者知道答案的冷门 corner case。

## 行为评分（取代纯计数）

`v5/behavior_manifest.json` 把 **33 个 behavior → 测试**；behavior 只有在**其全部
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
| `v5ref`（v2.4.1 reference） | 68/68 | **1.000** | 80/81（仅 d127 有意 supersede） | ~18s |
| `v5seed`（broken seed，低分基线） | 17/68 | **0.091** | 37/81 | ~17s |
| 语法错误注入（collection error） | 0/68 | 0.000 | 0/81 | — |

> 升级前曾用旧 v2.3 参考实现（`gold`/`gold2`）作为“代理能力”梯度参照，在
> v2.4.0/66 项套件上测得 `gold2` 35/66、`gold` 33/66。这些参考实现与其分数已随
> 旧基线一并清理，需要时从 git 历史 `aa2d0a8` 取回；仅作历史记录，不参与 V5 评分。

mutation sanity：`python mutation_check.py` 对 reference 施加 9 类单点 mutation
（only-last-filter / filter-after-unit / fail→skip / partial-output /
`temp or temperature` / broad-except / dedupe-keep-first / skip→exit1 /
nonfinite-as-null），**9/9 全部被捕获**（详见 `results/v5_mutation_check.json`）。

**注意**：上表只有 reference / seed 的校准值；首个真实模型跑分见「V5 leaderboard」。
其余候选仍须用 v2.4 任务书 + `v5seed` 重测后方可入榜。

### V5 leaderboard（v2.4.1 / 68 项，当前）

| 候选 | V5 raw /68 | behavior | legacy /81 | n | 日期 |
|---|---:|---:|---:|---:|---|
| `space-bunny-free` @ max（reasoning-effort 扫描最佳档） | **68.00 ± 0.00** | **1.000** | **80.0** | 5 | 2026-10-11 |
| `space-bunny-free` @ xhigh | 67.80 ± 0.45 | 0.994 | 80.0 | 5 | 2026-10-11 |
| `space-bunny-free` @ high | 67.60 ± 0.55 | 0.988 | 80.0 | 5 | 2026-10-11 |
| `space-bunny-free` @ medium | 67.20 ± 1.79 | 0.976 | 79.6 | 5 | 2026-10-11 |
| `space-bunny-free` @ low | 66.60 ± 2.07 | 0.958 | 79.4 | 5 | 2026-10-11 |
| `v5ref`（v2.4.1 reference，非候选） | 68 | 1.000 | 80 | — | — |
| `v5seed`（broken baseline，非候选） | 17 | 0.091 | 37 | — | — |

> 上表是 **v2.4.1 / 68 项**下的当前榜单。@ max 档在 5 次重复中全部拿到 68/68、
> behavior 1.000、legacy 80/81——**与参考实现 `v5ref` 完全持平**。
> 其余候选仍须按同一协议重测后方可入榜。
> v2.4.0 / 66 项下的首轮跑分保留在下方历史区，**不可**与本表并列。

### V5 leaderboard（v2.4.0 / 66 项，legacy）

| 候选 | V5 raw /66（v2.4.0） | behavior | legacy /81 | n | 日期 |
|---|---:|---:|---:|---:|---|
| `space-bunny-free`（reasoning-effort 扫描，5 档均值） | **65.4** | **0.981** | 80.0 | 5 | 2026-10-04 |
| `space-bunny-free` @ high（单次最佳档） | 65.40 ± 0.55 | 0.981 | 80.0 | 5 | 2026-10-04 |
| `v5ref`（v2.4 reference，非候选） | 66 | 1.000 | 80 | — | — |
| `v5seed`（broken baseline，非候选） | 17 | 0.094 | 37 | — | — |

> ⚠️ **本表全部数字是 v2.4.0 / 66 项套件下的历史结果，已被 v2.4.1 勘误 supersede**，
> 不可与 v2.4.1 / 68 项的新分数并列。原因见下方「v2.4.1 勘误」：这批 run 撞上了
> §3 规格笔误（`test_i3` 16/25 失败）与非有限值覆盖缺失；需在 v2.4.1 下重跑才能
> 作为当前榜单。旧 legacy 榜分数已清理，且**不可**迁入此表。
> 本表首行为 5 档 reasoning-effort 的均值，**不是**某一档的单次成绩。

### v2.4.1 勘误（2026-10-04）

首轮真实模型跑分（PR #5）暴露两处基准缺陷，按该 PR 建议以独立、可审计的修订修复：

1. **§3 validation/dedupe 表述自相矛盾**：原文写「更早的那条**不会**补位」，与冻结
   顺序图、参考实现、`test_i3` 及 legacy `gold2` 行为全部相反（它们都保留更早的
   合法记录）。这是笔误，已改正。它解释了该轮最大的方差来源——`test_i3` 单独
   16/25 失败，且五档均匀分布（候选照错误句子实现了）。
2. **非有限值（`nan`/`inf`）未规定也未测试**：25 次里 4 次把 `temp:"nan"` 归一为
   `null` 后保留（legacy `d11` 会拒绝）。§6/§10 已明确其为 record-level invalid，
   `v5/adversarial` 增加 `a13`/`a14` 两个用例，补齐 legacy 81 项语义。

修订范围：spec 文本、2 个新测试、behavior manifest（+1 behavior）、grader 固定
expected 数（66→68）。`v5ref` 未改动（原实现已符合修正后的语义），
`spec/FROZEN_HASHES.txt` 已重新生成。

**勘误修复效果已在 v2.4.1 下复测确认**（25 次运行，见下节）：满分率 28% → 72%，
`test_i3` 失败 16/25 → 0/25，非有限值静默写成 null 的运行 4/25 → 0/25。

## 附加实验：reasoning-effort 扫描（space-bunny-free，V5 **v2.4.1 / 68 项**，n=5）

这是勘误修复后的复测，**同一模型、同一 overlay、同一协议**，与下方 v2.4.0 那轮逐档可比。
盲测、one-shot、逐字节 `v5seed` 副本、交付后宿主侧 `grade_v5.py` 统一评分，
**每档 n=5（25 次运行，0 次被剔除）**。

| effort | V5 raw /68 逐轮 | 均值 ± sd | behavior | legacy /81 |
|---|---|---:|---:|---:|
| low | 63 / 67 / 68 / 68 / 67 | 66.60 ± 2.07 | 0.958 | 79.4 |
| medium | 68 / 68 / 64 / 68 / 68 | 67.20 ± 1.79 | 0.976 | 79.6 |
| high | 68 / 68 / 67 / 67 / 68 | 67.60 ± 0.55 | 0.988 | 80.0 |
| xhigh | 68 / 68 / 68 / 67 / 68 | 67.80 ± 0.45 | 0.994 | 80.0 |
| **max** | **68 / 68 / 68 / 68 / 68** | **68.00 ± 0.00** | **1.000** | **80.0** |

跑分前校验：26/26 frozen sha256 通过；校准逐位复现 `v5seed` 17/68 · 0.091 · 37/81、
`v5ref` 68/68 · 1.000 · 80/81。

**三处结构性变化（相对 v2.4.0 那轮）**：

- **满分率 7/25 (28%) → 18/25 (72%)**；`max` 从 1/5 满分变成 **5/5 满分**，
  behavior 1.000、legacy 80/81，与参考实现持平（v2.4.0 时它在 legacy 上稳定垫底 78.6）。
- **档位排序从混乱变成严格单调**：v2.4.0 是 max 垫底、medium 最低；
  v2.4.1 是 low < medium < high < xhigh < max，无一例外。
- **方差从集中变分散**：`test_i3` 的 16/25 归零，现在最高频的 `test_c7` 也只有 4/25。

**勘误效果的三项独立验证**：

| 验证项 | v2.4.0 | v2.4.1 |
|---|---:|---:|
| `test_i3_validation_before_dedupe` 失败 | 16/25 | **0/25** |
| 新增 `a13`/`a14`（非有限值）失败 | — | **0/25** |
| 实测把 `"nan"`/`"inf"` 静默写成 `temp:null` 并输出 | 4/25 | **0/25** |

**effort 效应：方向可信，强度仍不足**。组间置换检验 raw / behavior 均 **p = 1.000**
（组间跨度 1.40 分仍落在合并组内 sd 1.26 之内）；但按 25 次运行做的**趋势检验**
给出 Spearman **rho = 0.399、p = 0.051**——五档均值首次严格单调。
两个检验答案不同是因为问的不是同一个问题：组间检验问「任意两档是否有差异」，
趋势检验问「分数是否随 effort 单调上升」，后者才是本实验该问的问题。
结论应克制：**方向已清楚，但 1.4 分的效应在 25 次运行里仍压不住噪声**，
不足以宣称 effort 有效；需要 n≥10 或更难的任务。

**给基准设计的启示**：规格自相矛盾会让「模型能力」与「阅读理解」混在一起，
且这种噪声**不会**表现为某个档位更差，而是随机散布在全部档位上——
只看均值 ± sd 完全看不出来，必须逐测试归因才能定位。
建议把「逐测试失败频次分布」列为常规审计项。

证据（25 次运行的逐档逐轮分数、行为明细、失败清单、5 档 overlay、运行与评分脚本、
勘误前后对照脚本、完整性审计）见
[`results/model-harness-effort-v241/`](results/model-harness-effort-v241/)。
该目录已脱敏（本机绝对路径与用户名替换为占位符），评分数据未作任何改动。
本 PR **未改动任何 frozen artifact**：26/26 sha256 复验通过。

## 附加实验：reasoning-effort 扫描（space-bunny-free，V5 **v2.4.0**，n=5）

> 结果基于 **v2.4.0 / 66 项**套件，已被 v2.4.1 勘误 supersede（见上）。
> 保留为「首轮实测」的历史证据；结论（饱和、effort 无分离度）需在 v2.4.1 下复测。

同一模型跑满全部 5 档 `reasoning_effort`，协议与历史完全一致：盲测、one-shot、
逐字节 `v5seed` 副本、交付后宿主侧 `grade_v5.py` 统一评分。
**每档 n=5（25 次运行，0 次被剔除）**——本节是重复测量，与上表所有 one-shot 行不同。

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
  本模型远高于设计文档预期的 50–80% raw band。
- **方差几乎全部来自一个测试**：`test_i3_validation_before_dedupe` 单独占
  **16/25** 次失败，且五档分布几乎均匀（3/3/3/3/4），与 effort 无关。
  → 已定位为 §3 规格笔误（见「v2.4.1 勘误」），v2.4.1 已改正，需复测。
- **`max` 在 legacy 上稳定落后**（78.6，5 次里 4 次 78–79）：见下条。
- **V5 漏检非有限值**：`v5/*/test_*.py` 对 `nan`/`inf` 的字面覆盖为 **0 处**，
  v2.4 任务书也从未提及非有限值。25 次中有 4 次把 `temp:"nan"` 归一为 `temp: null`
  并写入输出（`max` 3/5、`xhigh` 1/5），而这些运行的 V5 分数是 64–66。
  → 已在 v2.4.1 修复：§10 明确非有限值为 record-level invalid，
  `v5/adversarial` 增加 `a13`/`a14` 两个用例覆盖该语义。

证据（25 次运行的逐档逐轮分数、行为明细、失败清单、5 档 overlay、
运行与评分脚本、完整性审计）见
[`results/model-harness-effort/`](results/model-harness-effort/)。
该目录已脱敏（本机绝对路径与用户名替换为占位符），评分数据未作任何改动。

# V7：校准后的区分度 tier（calibration-driven）

前三轮给出了三个负结果：V5 full-spec 饱和、V5-Minimal 信息消融无效、V6 在 40 tool
calls 预算下同样 9/9。V7 因此**反向设计**——不再扩张 spec / 测试 / micro-repo，而是回到
旧 V1–V4，先测量它为什么仍有区分度，再按测量结果重建。

## 为什么回到 V1–V4

当前 Flash population 在旧套件上的实测（6 个 model family × n=3 = 18 次运行；
旧任务条件逐字节恢复；基线先复现 seed 25/81 · gold 76/81 · gold2 81/81）：

| candidate | legacy /81 |
|---|---:|
| `hy4-preview-f` | 71.3 |
| `deepseek-v4.1-flash` | 68.3 |
| `grok-4.7` | 63.3 |
| `gemini-3.5-flash` | 60.3 |
| `minimax-m3` | 54.3 |
| `kimi-k2.6` | 52.0 |

**跨 family 跨度 19.3 分，档内 sd 2.5**；同期 V5 v2.4.1 上只有 1.4 分跨度。
旧方法论在当前 population 上仍然有效。

## 三个实测结论

1. **旧 raw /81 并没有放大 hard behaviours。** 81 个测试映射到 24 个语义行为，
   `correlation(n_tests, fail_rate) = 0.130` —— 几乎没有关系。重复集中在容错/管道类
   （`ndjson_malformed_tolerance` 独占 7 槽），而最难的那项只有 1 槽。
   81 个槽位里只有约 24.6 个是"活的"。
2. **旧套件的 7 个 floor item 是规格缺口，不是难度。** 任务书把 `--filter` 与
   `--unit` 列为两条互不相干的 bullet，**从未说明先后顺序**；md 转义同样从未提及。
   6 个 family 全部按另一种读法实现，于是这些 item 的 between-model variance 为零。
3. **把规则写进任务书后，它们从 p=0.06 直接变成 p=1.00** —— 三个行为全部从"没人过"
   变成"所有人都过"。**在两种状态下它们都不测能力**：之前测的是有没有猜中未公布的
   规则，之后什么都不测。

> 可推广的判据：**隐藏项的规则若无法从可见契约推出，它产生的分数看起来像难度、
> 行为像抛硬币；补上契约不会让它有区分度，只会删掉它。**

## V7 构成（post-pilot，未 freeze）

一个行为一个文件，行为级评分（一个行为的全部测试通过才算满足），三档显式权重
（basic 1 / inference 2 / hard 3），**不按测试重复买权重**。

| behaviour | tier | pilot p | var_between | var_within | 判定 |
|---|---|---:|---:|---:|---|
| `whitespace_trimming` | basic | 0.67 | 0.333 | 0.000 | **live** |
| `timestamp_microseconds_preserved` | inference | 0.50 | 0.250 | 0.167 | **live** |
| `bool_is_not_numeric` | inference | 0.50 | 0.250 | 0.167 | **live** |
| `legacy_temperature_fallback` | inference | 0.33 | 0.083 | 0.333 | noise |
| `nonfinite_rejected` | inference | 0.50 | 0.000 | 0.500 | noise |
| `cli_exit_codes` | regression | 1.00 | 0 | 0 | ceiling |
| `csv_dialect_robustness` | regression | 1.00 | 0 | 0 | ceiling |
| `cli_full_chain` | regression | 1.00 | 0 | 0 | ceiling |
| `filter_unit_order` | regression | 1.00 | 0 | 0 | ceiling |
| `md_table_escaping` | regression | 1.00 | 0 | 0 | ceiling |

锚点（5 个计分行为）：**seed 0.000 / gold 0.778 / gold2 1.000**。
锚点只说明 tier 被锚定，**不**说明它难 —— V5 已经证明这个 proxy 是错的。

pilot（3 family × n=2）：

| candidate | r1 | r2 | mean |
|---|---:|---:|---:|
| `hy4-preview-f` | 0.778 | 0.556 | **0.667** |
| `deepseek-v4.1-flash` | 0.556 | 0.778 | **0.667** |
| `minimax-m3` | 0.000 | 0.222 | **0.111** |

## 状态：NOT READY TO FREEZE

必须如实记录失败面：

1. **两个强 family 打平**（均 0.667）——最需要分辨率的区间没有分辨率。
2. **档内方差仍高**：`nonfinite_rejected` 的 var_within 0.5 对 var_between 0.0，
   纯抖动、不区分任何模型。真正 live 的只有 3 个行为。
3. **跨任务书修订的分数不可比**：同一批产物在旧书下 0.10–0.60，新跑在新书下 0.00–0.78。

**结构性结论**：删掉假难度后信号也少了一大半。排除规格缺口后，当前 Flash 之间真正
可从契约推出的区分度**确实很薄**，集中在字段裁剪、数值精度、类型严格性三处。
这比 legacy 原始数字更接近"模型能力已跨过旧任务复杂度"。

## 后续条件

1. 诚实地扩充 live 集（3 个不足以排序）：候选是修 noise 行为的探针设计，以及新的
   契约可推导 closure probe，**不是**新的规格缺口项。
2. 增加第二个任务族：现有 V7 行为全在 datapipe 上，模型已反复见过。
3. 引用任何 V7 榜单前跑完整 population（6 family × n=3）。
4. 不要丢掉 legacy 套件 —— 排除规格缺口后它是项目里校准最好的工具，
   V7 是它 live 核心的重新加权，不是替代品。

## V7 产物

| 路径 | 内容 |
|---|---|
| `v7/` | 10 个 behaviour（一行为一文件）+ conftest + behavior_manifest（含 anchor / provenance / pilot 判定） |
| `v7/ONBOARDING_TODO.md` | V7 任务书 = v2.3 + 两处规格修补 |
| `grade_v7.py` | 行为级加权评分器（固定分母，collection error 不缩分母） |
| `results/v7-calibrated-tier/` | 证据包：Phase 1–3 报告、18 次 legacy 评分、pilot 评分、锚点、行为映射与 item 分析、全部脚本（已脱敏） |

**未改动任何 frozen artifact**：`spec/`、`v5/`、`v5ref/`、`v5seed/`、`grade_v5.py`、
`mutation_check.py` 全部未触碰，`spec/FROZEN_HASHES.txt` 26/26 复验通过。

---

## 仓库内 frozen artifact

| 路径 | 内容 |
|---|---|
| `spec/ONBOARDING_TODO_v2.4.md` | candidate 任务书（逐字节复制进候选工作区） |
| `spec/V5_DESIGN.md` | 设计依据、provenance、校准、风险、开发记录 |
| `spec/FROZEN_HASHES.txt` | spec / tests / reference / seed / grader 的 sha256 |
| `v5ref/` | v2.4 reference 实现（全绿） |
| `v5seed/` | plausible-but-wrong broken seed（低分基线） |
| `v5minseed/` | V5-Minimal 候选工作区（信息消融实验，代码与 `v5seed` 逐字节相同） |
| `v6/` | V6 三个微型任务 prototype（ref / seed / hidden / public） |
| `v5/behavior_manifest.json` | behavior → tests 映射与评分方法 |
| `grade_v5.py` / `mutation_check.py` | V5 评分器 / mutation 审计 |
| `grade_v6.py` | V6 评分器 |

## 局限（V5）

- `--on-error` 默认值、`DataError` 不继承 `ValueError` 属 **policy choice**，已写入 spec。
- `skip → exit 0` 与 legacy `d12::test_d127` 冲突，是 v2.4 有意演进，legacy 保持冻结。
- **首个模型已触及顶部饱和**：`space-bunny-free` 在 v2.4.0 下均分 64.2–65.4/66，
  本套区分度对强 Flash 已接近 0；但该轮撞上 §3 规格笔误，**结论须在 v2.4.1 下复测**。
  若复测仍饱和，下一步应是更难的 contract（V6），而不是继续加同类测试。
- **已复测（V5-Minimal 信息消融）**：v2.4.1 下 9/9 满分，证明饱和不是任务书过详所致；
  V5 作为「合规性 tier」保留，不再作为区分度来源。区分度实验转入 V6（见上）。
- 非有限值覆盖已于 v2.4.1 补齐（spec §6/§10 + `a13`/`a14`）。

---

# 实验：V5-Minimal（信息消融）

> **问题**：V5 顶部饱和，是因为任务**太简单**，还是任务书**过度详细**（等于给了
> implementation checklist）？

`spec/V5_MINIMAL.md` + `v5minseed/`。控制实验：**同 seed 代码（与 `v5seed`
逐字节相同）、同 hidden 测试、同 grader、同工具权限**，只替换 candidate 可见信息
——315 行逐条 spec 换成 36 行维护者 brief，contract 改由 README / CHANGELOG /
docs/ / examples/ 分散承载（每个 hidden behavior 至少 2 个独立证据来源，
provenance 审计见 `spec/V5_MINIMAL.md` §4）。

| 条件 | 模型 | n | V5 raw | behavior |
|---|---|---:|---:|---:|
| full-spec V5（v2.4.0/66） | space-bunny-free | 25 | 64.2–65.4 | 0.94–0.98 |
| **V5-Minimal（v2.4.1/68）** | space-bunny-free | **9** | **68/68 ×9** | **1.000 ×9** |

**结论：减少信息没有降低分数——9/9 全部满分。** 轨迹显示模型自行从 CHANGELOG +
docs + 源码重建了 contract（8/9 读全 docs，1 次只读 CHANGELOG+源码即达 68/68）。
→ V5 饱和**不是** over-specification；对强 Flash，datapipe 类「单任务 contract
重建」已被吃透。详细结果与 caveat 见
[`results/v5-minimal-pilot/RESULT.md`](results/v5-minimal-pilot/RESULT.md)。

---

# 原型：V6（多任务 inference tier）

> **不再往 datapipe 堆 corner case。** V6 换轴：在**固定工作预算**下，从仓库证据
> 恢复程序语义、修复非局部问题。

`spec/V6_PROTOTYPE.md` + `v6/`。三个独立微型 repo（stdlib only，~200–350 LOC），
各测不同认知结构，短 `ISSUE.md`（只给症状，不给修法），public 套件**故意对深层
behavior 盲**（seed 能全过 public 但 hidden 低分）：

| task | 认知结构 | ref | seed behavior | seed public |
|---|---|---:|---:|---:|
| `taskA_ledger` | 原子性 + 不变量推理 | 1.000 | 0.444 | 5/5 |
| `taskB_framecodec` | 字节流状态机（任意 chunk 切分） | 1.000 | 0.167 | 6/6 |
| `taskC_cfgmerge` | 分层优先级推理 | 1.000 | 0.286 | 6/6 |

Pilot（`space-bunny-free`，budget 40 tool calls，n=3/task）：**9/9 behavior 1.000**，
仍饱和。把预算压到 **12 tool calls** 才出现本轮唯一的真实 reasoning 失败：
`taskB` 0.833（escape 跨 chunk 状态机），taskA/taskC 仍在预算内解出。
→ 区分度可能在**预算轴**而非任务数轴上，V6 **NOT READY TO FREEZE**。
详见 [`results/v6-pilot/RESULT.md`](results/v6-pilot/RESULT.md)。

---

# 遗产套件：V1–V4 / datapipe v2.3（81 项）

> **状态：legacy / superseded。** 仅保留**测试套件** `d10 d11 d12 t2 t3 t4 v4`，
> 冻结不改，用于回归对照与历史方法论的溯源。
>
> **已清理**（随本次升级一并移除）：
> - 旧跑分结果 `results/space-bunny-free-effort-sweep/`（含 leaderboard 与
>   effort 扫描证据）；
> - 旧参考基线 `gold/`、`gold2/`；
> - 旧评分器 `grade_v3.ps1`（其能力已由 `grade_v5.py` 的 legacy 分项覆盖）。
>
> 以上均可在 git 历史 `aa2d0a8`（V5 之前的最后提交）中取回。它们跑在 v2.3 规格
> 与外部 v2.2.1 seed 上，分母/任务书/seed 与 V5 全不同，分数**不可**与 V5 并列。
> 说明见 [`results/LEGACY.md`](results/LEGACY.md)。

## 遗产套件构成（保留）

| 套件 | 测试数 | 考察点 |
|---|---:|---|
| d10 / d11 | 22 | 常规边界 + 规格推导（时区/微秒/负值/幂等/CLI 链） |
| d12 | 10 | 对抗性健壮性（坏行容错、bool 陷阱、数组输入、md 转义、退出码） |
| t2 / t3 / t4 | 25 | 分级能力 + 规格缺失推断（MIXED 族） |
| v4 | 24 | V4 核心区分（v4core 规格完整性 8 + 全量 16） |

套件仍可单独运行（需自备候选仓库）：

```bash
DATAPIPE_REPO=<候选仓库根> python3 -m pytest d10 d11 d12 t2 t3 t4 v4 -q
```

`grade_v5.py` 也会把 legacy 81 项作为独立分项一并报告，便于回归对照。

## 为什么被 supersede

旧套件把「单点边界 → 局部修复」做到极致后，强 Flash 已到 75–79/81 的顶部饱和；
且单一语义被多个测试重复覆盖，raw `/81` 带有隐式重复加权。这正是 V5（datapipe
v2.4）升级的直接动因。旧套件的完整方法论与实测结论保留在 git 历史 `aa2d0a8` 的
README 中。

## License

MIT。套件源于 DeepSeek Harness 消融实验方法论（V1–V5 分级迭代）。

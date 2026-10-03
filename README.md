# ablation-eval-v3

[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![dsh](https://img.shields.io/badge/dsh-0.1.0--rc.6-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![V5](https://img.shields.io/badge/V5%20tests-66-green)]()
[![legacy](https://img.shields.io/badge/legacy%20tests-81-lightgrey)]()

轻量、零依赖的 **DeepSeek V4 行为区分度分级套件**：用一个小型 datapipe 修复任务，
把基于 dsv4 的 Harness / Agent 工作的真实效果差异压进分数。

- **当前基准：V5（datapipe v2.4）** — 66 项组合语义测试 + 行为评分，见下。
- **遗产套件：V1–V4（datapipe v2.3，81 项）** — 测试套件保留冻结，结果、参考基线与
  旧评分器已移除，见文末。

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
| `v5seed`（broken seed，低分基线） | 17/66 | **0.094** | 37/81 | ~19s |
| 语法错误注入（collection error） | 0/66 | 0.000 | 0/81 | — |

> 升级前曾用旧 v2.3 参考实现（`gold`/`gold2`）作为“代理能力”梯度参照，测得
> `gold2` 35/66、`gold` 33/66。这些参考实现与其分数已随旧基线一并清理，
> 需要时从 git 历史 `aa2d0a8` 取回；当时数值仅作历史记录，不参与 V5 评分。

mutation sanity：`python mutation_check.py` 对 reference 施加 8 类单点 mutation
（only-last-filter / filter-after-unit / fail→skip / partial-output /
`temp or temperature` / broad-except / dedupe-keep-first / skip→exit1），
**8/8 全部被捕获**（详见 `results/v5_mutation_check.json`）。

**注意**：表中只有 reference / seed 的校准值，**尚无真实模型 V5 跑分**。
正式 V5 leaderboard 须在 frozen suite 之后，按与历史一致的盲测 one-shot 协议重跑
全部候选后方可发布。

### V5 leaderboard

| 候选 | V5 raw /66 | behavior | legacy /81 | 日期 |
|---|---:|---:|---:|---|
| _（待重测：所有候选须用 v2.4 任务书 + `v5seed` 重跑）_ | — | — | — | — |

> 旧榜分数已清理，且**不可**迁入此表。切换 benchmark 后所有候选必须全面重测。

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

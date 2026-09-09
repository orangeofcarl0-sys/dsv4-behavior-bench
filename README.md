# ablation-eval-v3

[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![dsh](https://img.shields.io/badge/dsh-0.1.0--rc.6-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-81-green)]()

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
| m1-router（m1 路由预设） | 76 | 25 | 11 | 11 | 5 | 8 | 6 | 11 | 24 |
| **opencode-go / omen-alpha** | **71** | 25 | 11 | 11 | 9 | 7 | 6 | 9 | 18 |
| **deepseek-v4.1-flash-expires-on-0910** | **71** | 25 | 10 | 11 | 10 | 7 | 6 | 9 | 18 |
| deepseek-v4-flash | 66 | 25 | 11 | 11 | 10 | 7 | 6 | 8 | 13 |
| deepseek-v4-flash-vision-exp | 65 | 25 | 11 | 10 | 10 | 7 | 6 | 8 | 13 |

- **public 全部 25/25**：公开测试对模型差异完全不敏感——这正是本套件存在的理由。
- **分离器是 d12 与 v4**：m1-router 的 d12 仅 5/10（对抗健壮性退化），模型候选 9-10/10；
  但 m1-router 的 v4 为 24/24，模型候选只有 18/24。
- omen-alpha 与 v4.1-flash 总分相同（71），10 项失败中 9 项重叠（legacy temperature 映射、
  NDJSON 坏行 skipped 计数、BOM 等规格外推断边界）；唯一分离点是 d12
  `test_d127_cli_transform_malformed_exit1`（omen-alpha 把坏行按跳过计数、退出 0）与
  d10 `test_d104_filter_whitespace_padded`（v4.1-flash 失败）。
- 运行日期：v4-flash / v4-flash-vision-exp 为 2026-08-21；omen-alpha / v4.1-flash-expires-on-0910 为 2026-09-09。
  每候选仅一轮（one-shot），未做方差测量，1-2 分差距应视为噪声级。

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

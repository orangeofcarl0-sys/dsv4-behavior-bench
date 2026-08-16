# ablation-eval-v3 — DeepSeek Harness 消融实验分级套件（datapipe）

DeepSeek Harness 社区预设（minimal-plus / routing-suite / anchored-standard）机制消融实验的 **datapipe 任务分级评分套件**。
public/heldout 全绿无区分度，本套件（81 个分级测试）提供可判别的能力分层。

## 结构

| 套件 | 测试数 | 考察点 |
|---|---|---|
| d10 | 11 | 常规边界回归（时区/微秒/负值过滤/空目录/幂等/CLI 链） |
| d11 | 11 | 规格边界与规格推导 |
| d12 | 10 | 对抗性健壮性（transform/emit 坏行容错、bool 陷阱、数组输入、md 转义、退出码） |
| t2 | 8 | 任务-轨迹关联（规格推断） |
| t3 | 6 | 分级能力基准 |
| t4 | 11 | 规格缺失项推断（MIXED 族思路） |
| v4 | 24 | V4 核心区分（v4core 8 题规格完整性 + v4 16 题全量） |
| gold / gold2 | — | GOLD 参考实现（gold=原最强产物；gold2=修复版全过） |

## 校准与区分度（2026-08-16 实测，宿主评分）

| 候选 | d10 | d11 | d12 | t2 | t3 | t4 | v4 | 总分/81 |
|---|---|---|---|---|---|---|---|---|
| GOLD2（修复版） | 11 | 11 | 10 | 8 | 6 | 11 | 24 | **81** |
| GOLD（=m1-router 产物） | 11 | 11 | 5 | 8 | 6 | 11 | 24 | 76 |
| gw-anchored-r1 | 11 | 11 | 6 | 7 | 6 | 9 | 16 | 66 |
| pro-anchored-r1 | 11 | 11 | 6 | 7 | 6 | 9 | 14 | 64 |
| m2/m4/m5-r1 | 11 | 11 | 5 | 7 | 6 | 9 | 13 | 62 |
| **seed**（未修复基线） | 4 | 6 | 5 | 4 | 0 | 2 | 4 | **25** |

区分度：seed 25/81 → GOLD2 81/81，中间态 62-76 可排序。public/heldout 在这批候选上全部 25/25+8/8 饱和——**分级请以本套件为准**。

## 用法

### 方式 A：PowerShell 一键评分

powershell:
  powershell -File grade_v3.ps1 -Repo <候选datapipe仓库根> -Label <名字>
  # 例：powershell -File grade_v3.ps1 -Repo .\gold2 -Label GOLD2
  # 输出：public / heldout / d10-d12 / t2-t4 / v4 各行通过数

### 方式 B：pytest 直跑（容器/CI）

bash:
  DATAPIPE_REPO=<候选仓库根> python3 -m pytest <本仓库>/d10 <本仓库>/d11 <本仓库>/d12 <本仓库>/t2 <本仓库>/t3 <本仓库>/t4 <本仓库>/v4 -q

套件 conftest 从环境变量 `DATAPIPE_REPO` 解析候选仓库（默认回退到相对路径）；PYTHONPATH 无需手动设置（conftest 已注入）。

## 关联项目

- 消融实验设计与数据：见 dsh-routing-suite / dsh-anchored-standard 的机制消融
- 本套件为 datapipe 任务（Python 遥测数据管道 CLI）专用；2048 任务分级套件待建

## License

MIT。套件基于消融实验方法论开发（V1-V4 分级迭代：v4core/d10-d12 预校准门槛 + GOLD 对照）。

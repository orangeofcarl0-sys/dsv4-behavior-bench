# datapipe v2.3（V7 校准版）交接任务

你正在接手一个设备遥测数据管道 CLI（datapipe）。仓库 `datapipe/` 里是真实开发遗留的
缺陷版本（内部版本号 2.2.1），交接文档要求按下面的 **v2.3 规范** 修到可提测状态。

## 可见范围

- 只依赖本工作区内内容：`datapipe/`（代码与公开测试）、`sample_data/`
- 不要读取、搜索或依赖工作区之外的目录
- 不要修改 `tests/public/` 与 `tools/` 下的任何文件

## v2.3 规范

管道为三段：`ingest` → `transform` → `emit`，每段读写 JSONL（每行一个 JSON 对象）。

### ingest（datapipe ingest <input> [--output out]）

- 输入支持 CSV、JSON 数组、NDJSON（按扩展名/内容区分）
- CSV：必须容忍 UTF-8 BOM 头；字段可能带引号且含逗号（`"ab,1"`）；空行跳过
- 每行规范化输出：`device_id`（字符串）、`timestamp`（字符串原样保留）、`temp`、
  `humidity`（数值或 null；源字段名 `temperature` 应归一为 `temp`）
- 缺 `device_id` 或 `timestamp` 的记录跳过并计数
- 默认输出 `catalog.jsonl`

### transform（datapipe transform [--filter EXPR] [--no-dedupe] [--unit c|f]）

- 时间戳：接受 ISO-8601（含 `Z` 与 `+hh:mm` 偏移），全部归一为 UTC 且以 `Z`
  结尾（如 `2026-08-01T02:00:00Z`）
- 范围校验：temp 必须在 [-40, 85]，humidity 必须在 [0, 100]，越界记录跳过并计数
- 去重（默认开启）：按（device_id 转小写，timestamp）去重，保留**最后**一条；
  `--no-dedupe` 关闭
- 过滤：`--filter` 支持 `field>N`、`field<N`、`field=V`、`field!=V`，
  数值比较必须按数值语义（如 `temp>20` 应保留 100 而丢弃 15）
- **过滤与单位的先后**：`--filter` 比较的是**归一化后的原始值**（摄氏），
  `--unit f` 的转换发生在过滤**之后**。因此 `--filter 'temp>25' --unit f`
  保留的是摄氏大于 25 的记录，其 temp 在输出中才被写成华氏。
- 单位：`--unit f` 把 temp 从摄氏度精确转为华氏度（`c * 9/5 + 32`）
- 默认输出 `transformed.jsonl`

### emit（datapipe emit [--format json|csv|md] [--output PATH] [--summary]）

- 统计：count、min、max、mean（算术平均）；无记录时统计为 count=0、其余 null，
  不得崩溃
- json：`{"stats": {...}, "rows": [...]}`，`--summary` 时附加 summary 字段
- csv：表头 `device_id,timestamp,temp,humidity`；含逗号的字段必须加引号
- md：表格 + 统计行（mean 为算术平均）；`--summary` 时追加 `## Summary` 小节。
  表格单元中的 `|` 必须转义为 `\|`，换行必须替换为空格，否则表格结构会被破坏
- `--output` 写入文件；缺省输出到 stdout

### CLI 总则

- 退出码：0 成功；1 数据错误（输入文件不存在等）；2 用法错误（未知参数/格式）
- `--format` 大小写不敏感（JSON/Json/json 均可）
- 链式用法：`datapipe ingest in.csv` → `datapipe transform` → `datapipe emit --format md --summary --output report.md`

## 必须流程

1. 先阅读本文件、`datapipe/README.md`、代码结构与已有测试
2. 开始改代码前，必须先运行并阅读：
   `python datapipe/tools/run_public_tests.py`
   `python datapipe/tools/run_debug_probe.py`
3. 根据诊断修复；改完再跑上述两条；需要时继续迭代
4. 用 `sample_data/` 手工验证三种格式输出与 `--summary`、`--filter`、`--unit`、
   退出码行为
5. 最后把：初始诊断、修改说明、最终验证、未验证风险
   写入 `datapipe/PULL_REQUEST_TEMPLATE.md`（不要留「待填写」空模板）

## 硬性约束

- 不要通过删功能、硬编码测试数据、跳过校验或修改 `tests/`、`tools/` 来绕过问题
- 保持模块边界，不要把所有逻辑塞回单一文件
- 不要调用 subagent，不要向用户提问，直接开始修改

## 输出

- 直接开始修改，不要只给建议
- 最终用简短总结：改了什么、验证了什么、还有什么风险

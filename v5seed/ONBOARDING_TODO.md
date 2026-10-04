# ONBOARDING_TODO — datapipe v2.4（修订 v2.4.1）

> 本文件是 **frozen spec**。candidate 实际运行时看到的任务书必须逐字节复制本文件，
> 不允许存在「实验时一版、repo 里另一版」。修改本文件等价于发布新的 spec 修订：
> 勘误 / 澄清为 **v2.4.x**，新增 contract 为 **v2.5+**；每次修订必须同时更新
> `spec/V5_DESIGN.md` 与 `spec/FROZEN_HASHES.txt`。
>
> **v2.4.1（2026-10-04）勘误**：
> 1. §3 澄清 validation→dedupe 的实际语义。旧措辞「更早的那条**不会**补位」与冻结
>    顺序、参考实现及 v2.3 legacy 行为相反，属笔误；正确语义是「更早的合法记录
>    **会被保留**」。
> 2. §6 / §10 明确非有限数值（`NaN` / `Infinity` / `-Infinity`）为 record-level
>    invalid，不得归一为 `null` 保留（补齐 legacy `d11` 语义）。

你是本次 datapipe 修复任务的负责人。工作目录就是你的全部可见范围。
请先读完本文件，然后按「必须流程」章节直接开始修复 `datapipe/` 仓库。

---

## 1. 背景

`datapipe` 是一条设备遥测数据管道 CLI：

```
ingest  ->  transform  ->  emit
原始文件     规范化目录     清洗数据集     报告
```

v2.3 已经完成「单点边界修复」。v2.4 的目标不是增加功能数量，而是要求实现
**完整的管道心智模型**：跨模块 contract、算子顺序、错误语义、原子性、组合行为。
因此 v2.4 的规格重点在 **一致性** 与 **错误策略**，而不是新的数据格式。

仓库结构：

```
datapipe/
  __init__.py
  version.py
  errors.py        # 新增：错误类型
  ingest.py
  transform.py
  emit.py
  cli.py
tests/public/      # 公开测试（不得修改）
tools/             # 调试脚本（不得修改）
sample_data/       # 示例输入
```

---

## 2. v2.4 新增能力（本次任务的核心）

v2.4 在 v2.3 之上新增三项能力，并要求它们与既有语义**全链路一致**：

1. `--on-error skip|fail`：统一错误策略（CLI + library）。
2. **atomic output**：`fail` 模式下绝不留下 partial output。
3. **重复 `--filter`，AND 语义**：多个过滤器按 AND 组合，且顺序无关。

---

## 3. 处理顺序（frozen）

所有记录必须严格经过以下顺序。顺序本身就是 contract，不允许实现自由调整：

```
parse / normalize      # 解析 + 字段规范化（含 legacy 字段回退、类型归一）
        ↓
validation             # 范围校验（transform 阶段）
        ↓
dedupe                 # 去重，保留最后一次出现
        ↓
filter(s)              # 0..N 个过滤器，AND 组合，作用于「未做单位换算」的 canonical 值
        ↓
unit conversion        # 仅在 --unit f 时把 temp 由摄氏转华氏
        ↓
emit / serialize       # 序列化输出
```

由此推导出的**必须成立**的语义（这些是 contract，不是实现细节）：

- 所有 filter 都作用在 **unit conversion 之前** 的值上。`--filter "temp>25" --unit f`
  表示「摄氏温度 > 25」，而不是「华氏温度 > 25」。
- filter 作用在 **dedupe 之后**。被后一条 duplicate 替换掉的旧值，
  不得因为新值 filter 失败而「复活」。
- validation（范围校验）在 dedupe 之前：越界的记录**先被丢弃**，之后才做去重。
  因此若一条 duplicate 的最后一条越界，它在 dedupe 之前就已被移除；dedupe 只看到
  剩下的记录，更早的那条**合法**记录会被保留。（对照上一段：filter 在 dedupe
  **之后**，所以被 filter 淘汰的记录不会让更早的 duplicate 复活；两者顺序不同，
  结果也不同。）
- 多个 filter 是 AND，且与书写顺序无关：`A ∧ B` 与 `B ∧ A` 结果完全相同。

---

## 4. CLI contract

```bash
datapipe ingest <input> [--output catalog.jsonl] [--on-error skip|fail]

datapipe transform [--input catalog.jsonl] [--output transformed.jsonl] \
                   [--filter EXPR]... [--no-dedupe] [--unit c|f] \
                   [--on-error skip|fail]

datapipe emit [--input transformed.jsonl] [--output PATH] \
              [--format json|csv|md] [--summary] [--on-error skip|fail]
```

- `--on-error` 默认值为 `skip`（保持 v2.3 默认行为兼容）。
- `--filter` 可重复出现；多个 `--filter` 按 **AND** 组合。旧式单个 `--filter` 语义不变。
- `--format` 大小写不敏感（`JSON` == `json`）。
- `ingest` / `transform` 的 `--output` 有默认文件名；`emit` 的 `--output` 缺省表示写 stdout。

---

## 5. library contract

```python
from datapipe import ingest, transform, emit, DataError

ingest(path, out, on_error="skip") -> (accepted: int, skipped: int)

transform(catalog, out, filter_expr=None, dedupe=True, unit=None,
          filters=None, on_error="skip") -> (kept: int, skipped: int)

emit(records_path, fmt, out_path=None, summary=False,
     on_error="skip") -> (text: str, stats: dict)
```

- `filters` 是一个 **list**，等价于多个 `--filter`；与 `filter_expr` 同时给出时**合并**
  （即 `filter_expr` 相当于 `filters=[filter_expr]`），全部按 AND 组合。
- `filter_expr` 单参数调用必须继续可用（backward compatibility）。
- CLI 与 library 必须具有**等价语义**：同一份数据、同一 `on_error`，
  library 抛出的数据错误与 CLI 的退出码必须对应一致。

### 错误类型

新增并导出 `datapipe.DataError`（定义在 `datapipe/errors.py`，并从 `datapipe`
包顶层 re-export）：

- 用于表达 **record-level 数据错误**。
- 在 `on_error="fail"` 下，遇到第一个 record-level malformed 数据时抛出。
- `DataError` **不得**是 `ValueError` 的子类，以便「数据错误」与「用法错误」可区分。

---

## 6. 错误策略 `--on-error`

### `skip`（默认）

record-level malformed / invalid 数据：

- 跳过该 record；
- 计入 `skipped`（CLI 在 stdout/stderr 打印计数）；
- 继续处理其余有效数据；
- CLI 成功完成时 **exit 0**。

### `fail`

遇到**第一个** record-level malformed / invalid 数据：

- 立即停止；
- library 层抛出 `DataError`；
- CLI 映射为 **exit 1**；
- **不得留下新的 partial output**（见第 7 节）。

### 定义：fail = 在 skip 会跳过的第一条记录处停止

`fail` 与 `skip` 是严格对偶：**凡是 `skip` 会跳过并计数的记录，`fail` 都会在它处停止**。
这包括（不限于）：坏 JSON 行、非对象记录、缺失必填字段、时间戳不可解析、
数值越界。

### record-level malformed 的边界（必须区分）

- **不是** malformed（记录保留，字段归一为 `null`）：
  `temp` / `humidity` 非数值或不可解析、布尔值（JSON `true`/`false` 不是数值）、
  `temp` 为空串。
- **是** invalid（不是 malformed，但同样触发 `skip` / `fail`，**不得**归一为
  `null` 后保留）：`temp` / `humidity` 解析结果为**非有限数值**
  （`NaN` / `Infinity` / `-Infinity`）。
- **是** malformed：整个记录不可解析、非对象、缺 `device_id`/`timestamp`。

---

## 7. exit code

| 情况 | 退出码 |
|---|---|
| 成功（包括 `skip` 下跳过了若干记录） | **0** |
| 数据错误：输入文件不存在；或 `fail` 下遇到 record-level malformed | **1** |
| 用法 / 配置错误：未知参数、`--format xml`、`--unit k`、非法 `--on-error` 值、畸形 filter 表达式 | **2** |

**重要：**

- `skip` 下即使 `skipped > 0`，只要流程正常完成，退出码必须是 **0**。
- 畸形 filter 表达式属于 **用法错误（2）**，绝不能被当作 record-level 数据问题
  计入 `skipped` 或导致 exit 0。
- 不允许用 broad `except Exception` 把程序 bug 当成数据错误吞掉。

---

## 8. atomic output（核心能力点）

在 `on_error="fail"` 下，一旦处理失败：

- 若 output 原本**不存在** → 处理后 output **仍然不存在**；
- 若 output 原本**已存在** → 旧文件必须保持**原内容**，既不能被 truncate，
  也不能留下「前几条 valid record」。

示例（ingest / transform 的 `--output`，以及 `emit --output` 均适用）：

```
valid
valid
BAD      <- fail 在此停止
valid
```

处理失败后：output 不存在（或旧内容不变）。

允许的实现方式（不限定）：全量验证后再写、tempfile + atomic replace、其他等价方案。
测试只验证 externally observable contract，不锁死实现细节。

---

## 9. 多个 `--filter` 与 filter 表达式

filter 表达式语法（沿用 v2.3）：

```
field OP value
```

- `OP` ∈ `>=` `<=` `!=` `>` `<` `=`；
- 前后空白自由：`temp>20`、`temp >20`、`temp> 20`、`  temp > 20  ` 等价；
- 两侧都是数值时按**数值**比较，否则按字符串比较；
- 记录缺少该字段（值为 `null`）→ 该记录不匹配；
- 畸形表达式（无运算符、取值为空、取值以 `>` `<` `=` `!` 开头）→ 用法错误。

多个 filter 为 AND：

```bash
--filter "temp>=20" --filter "humidity<80"
```

等价于「两个条件同时成立」。

---

## 10. 字段与规范化规则（沿用 v2.3，v2.4 明确化）

- 支持 CSV / JSON（对象或数组）/ NDJSON；按扩展名选择，未知扩展名按内容嗅探
  （以 `{` / `[` 开头 → JSON/NDJSON，否则 CSV）。
- CSV：容忍 UTF-8 BOM；引号内逗号正确解析。
- `device_id` / `timestamp`：去除首尾空白；缺失或空白 → 记录 malformed。
- `device_id` 缺失时回退字段 `device`。
- `temp` 回退 legacy 字段 `temperature`，**回退条件**为：`temp` 缺失、为 `null`、
  或为空/空白字符串。特别注意：
  - `temp = 0` 是**合法数值**，不得回退到 `temperature`；
  - `temp = ""` / `temp = null` → 回退 `temperature`；
  - `temp = false`（布尔）→ 不是缺失，不回退；归一为 `null`。
- `temp` / `humidity` 归一为 `float` 或 `null`。
- **非有限数值不是合法取值**：`NaN` / `Infinity` / `-Infinity`（无论以 JSON 数值
  字面量还是字符串形式出现）都必须按 record-level invalid 处理——范围校验拒绝该
  记录（`skip` 下跳过并计入 `skipped`；`fail` 下抛出数据错误），
  **不得**归一为 `null` 后保留。
- transform 的时间戳归一为 UTC、以 `Z` 结尾的 ISO-8601，**保留微秒**。
- 范围校验：`temp ∈ [-40, 85]`，`humidity ∈ [0, 100]`；值为 `null` 时通过。
- dedupe key = (`device_id` 转小写, 归一后的 timestamp)，保留**最后一次**出现。
- `--unit f`：`F = C * 9 / 5 + 32`（精确公式）。
- `emit`：
  - json：`{"stats": {...}, "rows": [...]}`，可选 `summary`；
  - csv：表头 `device_id,timestamp,temp,humidity`，含逗号的字段必须加引号；
  - md：统计行 `mean` 必须是**算术平均**（不是 `(min+max)/2`）；表格单元中的
    `|` 必须转义为 `\|`，换行必须替换为空格；可选 `## Summary`。
  - `stats`：`count`（行数）、`min`/`max`/`mean`（仅统计非 `null` 的 temp；
    无有效 temp 时三者均为 `null`）。

---

## 11. backward compatibility（v2.3 → v2.4）

- `--on-error` 默认 `skip`；v2.3 的「跳过坏记录并继续」语义不变。
- `transform(..., filter_expr=...)` 单参数调用不变。
- `ingest(path, out)` / `emit(path, fmt, out_path=..., summary=...)` 调用不变。
- v2.3 已确立的字段规范化、dedupe、filter、unit、emit 语义全部保留。
- **唯一有意的行为变更**：v2.3 的 CLI 在 `transform` 有跳过记录时返回 exit 1；
  v2.4 明确为 **skip → exit 0**（见第 7 节）。这是一次 spec 演进，
  candidate 必须按 v2.4 实现。

---

## 12. 硬性约束

1. 不得删除或削弱既有功能（ingest/transform/emit 的 v2.3 行为必须保留）。
2. 不得硬编码测试数据、不得针对特定输入分支。
3. 不得跳过校验（范围、时间戳、必填字段）。
4. **不得修改 `tests/` 与 `tools/` 下的任何文件。**
5. 不得引入第三方依赖；只用 Python 标准库（Python ≥ 3.10）。
6. 保持 `ingest / transform / emit / cli` 四段模块边界，不得把管道塞进单文件。
7. 不得用 broad `except Exception` 吞掉程序 bug。

---

## 13. 必须流程

1. 先运行 `python3 tools/run_public_tests.py` 与 `python3 tools/run_debug_probe.py`，
   记录初始诊断。
2. 按第 2–10 节的 contract 修复实现，覆盖 `--on-error`、atomic output、
   多 filter、处理顺序。
3. 自行验证：public 测试全绿；并手工构造至少一个「NDJSON 坏行 + skip」与
   一个「fail + 已有 output」场景，确认退出码与文件状态正确。
4. 把初始诊断、修改说明、最终验证、未验证风险写入
   `datapipe/PULL_REQUEST_TEMPLATE.md`。
5. 结束时给出简短总结：改了什么、验证了什么、还有什么风险。

约束：只在当前工作目录内读写；一次性完成，不要停下来提问。

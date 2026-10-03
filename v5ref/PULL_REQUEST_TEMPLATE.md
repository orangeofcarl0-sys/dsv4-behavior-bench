# datapipe 修复交付报告

## 初始诊断

运行 `python3 datapipe/tools/run_public_tests.py`：**18 通过 / 7 失败**。
运行 `python3 datapipe/tools/run_debug_probe.py`：同 7 项失败；仓库内无 catalog.jsonl / transformed.jsonl（正常，未运行过管道）。

失败清单与定位：

| 失败测试 | 定位（代码行） | 根因 |
|---|---|---|
| test_cli_missing_input_exit_code | cli.py:37 | ingest 输入文件不存在时 `sys.exit(0)`，规范要求退出码 1 |
| test_cli_output_flag | cli.py:51 | emit 的 `--output` 被忽略（硬编码 `out_path=None`），且解析器未声明该参数 |
| test_cli_format_case_insensitive | cli.py:46-49 | `--format` 大小写敏感，`JSON` 被判为不支持并退出 2 |
| test_cli_summary_flag | cli.py:25-28 | emit 解析器缺少 `--summary` 参数 |
| test_cli_filter_wired / test_cli_unit_wired | cli.py:41-42 | `--filter`/`--unit` 解析后从未传入 transform 模块 |
| test_emit_csv_quoting | emit.py:24-37 | CSV 手工拼接，含逗号字段未加引号 |

代码中另有注释明示的遗留缺陷：md 统计行的 mean 用 `(min+max)/2`（非算术平均）；`--no-dedupe` 也未接线；版本号停留在 2.2.1。

## 修改说明

### datapipe/cli.py
- ingest：输入文件不存在改为 `error: <path>` 输出到 stderr 并 `return 1`（数据错误）。
- transform：把 `--filter`、`--no-dedupe`、`--unit` 实际传入 `transform_mod.transform()`；`FileNotFoundError`/`json.JSONDecodeError`（坏输入数据）→ 退出码 1；过滤器表达式错误（ValueError）→ 退出码 2（用法错误）。
- emit：补上 `--summary` 与 `--output` 参数；`--format` 先 `.lower()` 再做校验（大小写不敏感）；不支持格式 → 退出码 2；`--output` 写入文件（stdout 不再混入内容，计数走 stderr），缺省仍输出到 stdout；输入缺失/坏 JSONL → 退出码 1。

### datapipe/emit.py
- `_emit_csv`：改用 `csv.writer`，含逗号（或引号）的字段自动加引号，None 输出空串。
- `_emit_md`：统计行 mean 改为真正的算术平均（复用 `_stats` 的 mean），空数据时输出 `None` 而不崩溃。
- `emit()`：入口处统一 `fmt.lower()`，模块层与 CLI 层双保险。

### datapipe/ingest.py
- 新增 `_read_rows()`：按扩展名（.csv / .json / .jsonl / .ndjson）选解析器，未知扩展名按内容嗅探（`{`/`[` 开头走 JSON/NDJSON，否则走 CSV）。
- `_read_json()`：NDJSON 逐行解析，坏行不再崩溃，计数并入 skipped；单对象文件归一为单条。
- `device_id` 空串/空白时回退 `device` 字段；`temp` 缺失或空时回退 `temperature` 并归一；输出前 strip，保证 device_id/timestamp 为字符串。

### datapipe/transform.py
- `_match_filter()`：匹配后校验取值段非空且不以 `><=!` 开头，畸形表达式（如 `temp>>20`）抛 ValueError → CLI 退出码 2，而不是静默过滤全部记录。
- 其余（UTC 归一、范围校验、按小写 device_id+timestamp 去重保最后、数值语义过滤、`c*9/5+32` 华氏换算）经核对已符合 v2.3 规范，未改动。

### 版本
- `datapipe/version.py`、`datapipe/__init__.py`、`pyproject.toml` 同步为 2.3.0；`__init__` 改为从 `version.py` 单一来源导入。

未修改 `tests/`、`tools/` 下任何文件；模块边界保持 ingest/transform/emit/cli 四段结构。

## 最终验证

1. `python3 datapipe/tools/run_public_tests.py` → **25 passed**（修复前 7 failed）。
2. `python3 datapipe/tools/run_debug_probe.py` → **25 passed**，无异常输出。
3. sample_data 手工链式验证（`PYTHONPATH=/work/datapipe python3 -m datapipe.cli`）：
   - `ingest sample_data/telemetry.csv` → accepted=4, skipped=0，BOM/引号逗号测试通过；`telemetry.ndjson` → accepted=2。
   - `transform` → kept=3, skipped=1：temp=90 的 ef-3 被范围校验丢弃，`+08:00` 时间戳归一为 `02:15:00Z`。
   - `--filter 'temp>24'` → 仅保留 25.0（数值语义）；`--filter 'temp>=22.5'` → 3 条；`--filter 'device_id!=ab-1'` → 2 条。
   - `--unit f` → 22.5→72.5、23.1→73.58、25.0→77.0（精确公式）。
   - 去重：大小写不同的同设备同时间戳保留最后一条；`--no-dedupe` 保留两条。
   - `emit --format JSON --summary` → stdout 输出 `{stats, rows, summary}`，count=3、min/max/mean 正确。
   - `emit --format csv` → 表头 `device_id,timestamp,temp,humidity`；`"ab,1"` 正确加引号。
   - `emit --format md --summary --output report.md` → mean=23.533…（算术平均，非 (min+max)/2），末尾含 `## Summary`，文件写入成功、stdout 无内容。
   - 空输入 emit → count=0、min/max/mean=null，不崩溃。
   - 退出码：成功 0；输入缺失 1（ingest/transform/emit 均验证）；未知参数、`--format xml`、`--unit k`、坏过滤器 `temp>>20` → 2。
   - 无扩展名文件按内容嗅探为 CSV，`ingest` 正常。

## 未验证风险

- 无真实用户环境联调：仅在容器内 Python 3.13 + pytest 8.4 环境验证，未做 `pip install -e .` 后的 console-script（`datapipe` 命令）路径验证，`pyproject.toml` 的 `[project.scripts]` 条目仅静态核对。
- 无带微秒/毫秒小数秒时间戳的样本，`datetime.fromisoformat` 支持该格式但未用手工数据覆盖。
- NDJSON 中含非对象类型行（如字符串/数组）按“跳过并计数”处理、无 TZ 的裸时间戳按“不可解析跳过并计数”处理，这两类边界语义是依据规范推断，未在公开测试中覆盖。
- 极大规模输入的流式/内存表现未测试（当前实现整体读入内存）。
- Windows 路径/换行（CRLF CSV）未在 Linux 容器内验证。

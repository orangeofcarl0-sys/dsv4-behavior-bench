#!/usr/bin/env python3
"""make_v7_taskbook.py -- V7 task book = v2.3 book + the two spec fixes.

Fixes applied (both were measured spec gaps in Phase 2/3):
  1. state the filter/unit interaction order
  2. state md table escaping
Nothing else changes: the V7 tier deliberately keeps the *information level* of
v2.3 rather than the clause-by-clause V5 book, because V5-Minimal showed that
adding more visible specification removes the inference space.
"""
import os, shutil

W = os.path.dirname(os.path.abspath(__file__))
SRC = "<seed-root>/ONBOARDING_TODO.md"
DST = os.path.join(W, "bench", "v7", "ONBOARDING_TODO.md")

text = open(SRC, encoding="utf-8").read()

# fix 1: state the filter/unit order explicitly (it was two unlinked bullets)
old_filter = "- 过滤：`--filter` 支持 `field>N`、`field<N`、`field=V`、`field!=V`，\n  数值比较必须按数值语义（如 `temp>20` 应保留 100 而丢弃 15）"
new_filter = ("- 过滤：`--filter` 支持 `field>N`、`field<N`、`field=V`、`field!=V`，\n"
              "  数值比较必须按数值语义（如 `temp>20` 应保留 100 而丢弃 15）\n"
              "- **过滤与单位的先后**：`--filter` 比较的是**归一化后的原始值**（摄氏），\n"
              "  `--unit f` 的转换发生在过滤**之后**。因此 `--filter 'temp>25' --unit f`\n"
              "  保留的是摄氏大于 25 的记录，其 temp 在输出中才被写成华氏。")
assert old_filter in text, "filter bullet not found"
text = text.replace(old_filter, new_filter)

# fix 2: state md escaping
old_md = "- md：表格 + 统计行（mean 为算术平均）；`--summary` 时追加 `## Summary` 小节"
new_md = ("- md：表格 + 统计行（mean 为算术平均）；`--summary` 时追加 `## Summary` 小节。\n"
          "  表格单元中的 `|` 必须转义为 `\\|`，换行必须替换为空格，否则表格结构会被破坏")
assert old_md in text, "md bullet not found"
text = text.replace(old_md, new_md)

text = text.replace("# datapipe v2.3 交接任务",
                    "# datapipe v2.3（V7 校准版）交接任务", 1)

os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print("wrote", DST)
print("fix 1 applied:", "过滤与单位的先后" in text)
print("fix 2 applied:", "转义为" in text)
print("size: %d bytes (v2.3 original was %d)" % (len(text), len(open(SRC, encoding="utf-8").read())))

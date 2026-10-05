"""Behaviour: md table cells escape the pipe character.

This is the second FORMER SPEC GAP: the v2.3 task book said only
"md：表格 + 统计行（mean 为算术平均）" and never mentioned escaping, yet the legacy
suite scored it (p=0.06, zero between-model variance). The V7 task book states it.

Verdict UNMEASURED until the V7 pilot: the legacy number was measured under an
unstated spec and must not be reused.
"""
from conftest import emit_mod, read_jsonl, transform_mod, write_jsonl


def test_pipe_in_value_is_escaped(workdir):
    src = workdir / "in.jsonl"
    write_jsonl(src, [{"device_id": "a|b", "timestamp": "2026-08-01T00:00:00Z",
                       "temp": 20.0, "humidity": 45.0}])
    tr = workdir / "t.jsonl"
    transform_mod.transform(str(src), str(tr))
    text, _ = emit_mod.emit(str(tr), "md")
    body = [ln for ln in text.splitlines() if "a" in ln]
    assert body, f"no data row in md output: {text!r}"
    row = body[-1]
    assert "\\|" in row, f"pipe must be escaped, got {row!r}"
    assert "a|b" not in row, f"raw pipe must not appear unescaped, got {row!r}"

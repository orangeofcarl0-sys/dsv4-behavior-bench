#!/usr/bin/env python3
"""Summarize a V5-Minimal pilot: grade each workspace, aggregate, and compare
against the full-spec V5 distribution.

Usage: python analyze_v5min.py <logs-root> [<logs-root> ...]
Each <logs-root> holds <level>/ as a candidate workspace (post-run, modified in
place by the model) plus <level>.ndjson / <level>.rc.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parents[3]


def ndjson_stats(path):
    steps = tools = 0
    read_paths = set()
    if not path.exists():
        return {"steps": 0, "tool_calls": 0, "files_read": 0, "read_paths": []}
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.strip():
            continue
        try:
            ev = json.loads(ln)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "status" and ev.get("phase") == "step_end":
            steps += 1
        elif t == "tool_call":
            tools += 1
            tool = ev.get("tool")
            inp = ev.get("input") or {}
            for k in ("file_path", "path", "command"):
                v = inp.get(k)
                if v:
                    read_paths.add(f"{tool}:{str(v)[:120]}")
    return {"steps": steps, "tool_calls": tools,
            "files_read": len(read_paths), "read_paths": sorted(read_paths)}


def grade(ws, label):
    out = subprocess.run(
        [sys.executable, str(BENCH / "grade_v5.py"), str(ws), "--label", label],
        capture_output=True, text=True, cwd=str(BENCH), timeout=120,
    )
    return json.loads(out.stdout)


def main():
    roots = [Path(a) for a in sys.argv[1:]]
    all_rows = []
    for root in roots:
        for lvdir in sorted(root.iterdir()):
            if not lvdir.is_dir():
                continue
            lv = lvdir.name
            rep = root.name
            g = grade(lvdir, f"{rep}-{lv}")
            raw = g["v5"]["raw"]
            beh = g["v5"]["behavior"]
            stats = ndjson_stats(root / f"{lv}.ndjson")
            failed = {}
            for cat, cdef in beh["categories"].items():
                for bname, bd in cdef["behaviors"].items():
                    if not bd["satisfied"]:
                        failed[bname] = cat
            all_rows.append({
                "rep": rep, "level": lv,
                "v5_raw": raw["passed"], "v5_total": raw["total"],
                "behavior": round(beh["overall"], 4),
                "behaviors": f"{beh['behaviors_satisfied']}/{beh['behaviors_total']}",
                "legacy": f"{g['legacy']['raw']['passed']}/{g['legacy']['raw']['total']}",
                "public": f"{g['public']['passed']}/{g['public']['passed']+g['public']['failed']}",
                "failed_behaviors": sorted(failed),
                "steps": stats["steps"], "tool_calls": stats["tool_calls"],
                "files_touched": stats["files_read"],
                "runtime_s": g["runtime_seconds"],
            })
    print(json.dumps(all_rows, ensure_ascii=False, indent=2))
    out = Path(__file__).resolve().parent / "pilot_rows.json"
    out.write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()

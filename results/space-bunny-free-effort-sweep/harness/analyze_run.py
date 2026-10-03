#!/usr/bin/env python3
"""Summarize one headless run's NDJSON event stream (host-side only)."""
import json, sys, os, collections

def summarize(path):
    steps = 0; tool_calls = collections.Counter(); tools = []
    thinking_events = 0; text_chars = 0; final_text = ""
    turn_end = None
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            o = json.loads(ln)
        except Exception:
            continue
        t = o.get("type")
        if t == "status":
            if o.get("phase") == "step_start":
                steps += 1
            if o.get("phase") in ("turn_end", "done"):
                turn_end = o
        elif t == "thinking":
            thinking_events += 1
        elif t == "text":
            c = o.get("text") or ""
            text_chars += len(c); final_text = c
        elif t == "tool_call":
            name = o.get("name") or o.get("tool") or "?"
            tool_calls[name] += 1
            tools.append(name)
    dur = None
    d = os.path.dirname(path)
    try:
        dur = int(open(os.path.join(d, os.path.basename(path).split(".")[0] + ".end")).read()) - \
              int(open(os.path.join(d, os.path.basename(path).split(".")[0] + ".start")).read())
    except Exception:
        pass
    return {
        "log": os.path.basename(path),
        "steps": steps,
        "thinking_events": thinking_events,
        "tool_calls_total": sum(tool_calls.values()),
        "tool_calls": dict(tool_calls),
        "final_text_chars": text_chars,
        "wall_seconds": dur,
        "final_message": final_text[-1200:],
    }

if __name__ == "__main__":
    print(json.dumps(summarize(sys.argv[1]), ensure_ascii=False, indent=2))

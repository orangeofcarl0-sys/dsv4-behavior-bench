#!/usr/bin/env python3
"""scan_dirty.py -- objective cleanliness scan of every run across replicates.

Signals that mark a run as infrastructure-dirty regardless of its score:
  * non-zero exit code
  * stderr beyond the one known profile notice
  * transport/provider errors (429, rate limit, overload, socket/ECONNRESET, retry storms)
  * tool calls that errored
  * a stream with no turn_end / done marker (truncated session)
  * a run that produced no assistant text at all
"""
import collections, json, os, re, sys

W = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["low", "medium", "high", "xhigh", "max"]
REPS = [1, 2, 3]

ERR_PAT = re.compile(
    r"rate.?limit|\b429\b|overload|temporarily unavailable|ECONNRESET|EPIPE|socket hang up|"
    r"fetch failed|network error|retry|aborted|connection (closed|reset)|Timeout|timed out",
    re.I)
KNOWN_STDERR = "unconfined-bash hack"


def log_dir(rep):
    return os.path.join(W, "logs_v5" if rep == 1 else "logs_v5_r%d" % rep)


def scan(rep, lv):
    d = log_dir(rep)
    nd = os.path.join(d, lv + ".ndjson")
    out = {"rep": rep, "level": lv}
    rc_p, err_p = os.path.join(d, lv + ".rc"), os.path.join(d, lv + ".err")
    out["rc"] = open(rc_p).read().strip() if os.path.exists(rc_p) else "?"
    err = open(err_p, encoding="utf-8", errors="replace").read() if os.path.exists(err_p) else ""
    out["stderr_extra"] = [l for l in err.splitlines()
                           if l.strip() and KNOWN_STDERR not in l][:6]
    steps = thinking = text_events = 0
    tool_err = 0
    tool_calls = 0
    ends = 0
    err_hits = 0
    if os.path.exists(nd):
        with open(nd, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
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
                        ends += 1
                elif t == "thinking":
                    thinking += 1
                elif t == "text":
                    text_events += 1
                elif t == "tool_call":
                    tool_calls += 1
                elif t == "tool_result":
                    if o.get("status") not in ("completed", "ok", None):
                        tool_err += 1
                blob = ln
                if ERR_PAT.search(blob):
                    err_hits += 1
    out.update({"steps": steps, "thinking": thinking, "text_events": text_events,
                "tool_calls": tool_calls, "tool_errors": tool_err,
                "terminal_markers": ends, "transport_error_lines": err_hits})
    flags = []
    if out["rc"] not in ("0", "?"):
        flags.append("rc=%s" % out["rc"])
    if out["stderr_extra"]:
        flags.append("stderr")
    if err_hits:
        flags.append("transport_errors x%d" % err_hits)
    if tool_err:
        flags.append("tool_errors x%d" % tool_err)
    if ends == 0:
        flags.append("no_terminal_marker")
    if text_events == 0:
        flags.append("no_assistant_text")
    out["flags"] = flags
    return out


rows = []
for rep in REPS:
    for lv in LEVELS:
        if os.path.isdir(os.path.join(W, "runs_v5" if rep == 1 else "runs_v5_r%d" % rep, lv)):
            rows.append(scan(rep, lv))

print("%-12s %4s %6s %6s %6s %6s %5s %8s  %s" % (
    "run", "rc", "steps", "think", "calls", "toolErr", "ends", "errLines", "flags"))
for r in rows:
    print("%-12s %4s %6d %6d %6d %6d %5d %8d  %s" % (
        "rep%d/%s" % (r["rep"], r["level"]), r["rc"], r["steps"], r["thinking"],
        r["tool_calls"], r["tool_errors"], r["terminal_markers"],
        r["transport_error_lines"], ", ".join(r["flags"]) or "clean"))
dirty = [r for r in rows if r["flags"]]
print("\ndirty runs: %d/%d" % (len(dirty), len(rows)))
for r in dirty:
    print("  rep%d/%s -> %s" % (r["rep"], r["level"], r["flags"]))
    if r["stderr_extra"]:
        print("      stderr:", r["stderr_extra"][:3])
json.dump(rows, open(os.path.join(W, "logs_v5", "cleanliness.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("wrote logs_v5/cleanliness.json")

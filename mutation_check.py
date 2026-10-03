#!/usr/bin/env python3
"""Mutation sanity check for the V5 benchmark.

Takes the V5 reference, applies one targeted source mutation at a time, and
verifies the behavior score drops. This guards against a suite that is green
for the wrong reasons (a mutation that should be caught but isn't).

Usage:  python mutation_check.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE / "v5ref"
GRADER = HERE / "grade_v5.py"


def grade(repo):
    proc = subprocess.run(
        [sys.executable, str(GRADER), str(repo), "--label", repo.name],
        capture_output=True, text=True,
    )
    return json.loads(proc.stdout)


def _sub(path, old, new):
    p = REF / "datapipe" / path
    text = p.read_text(encoding="utf-8")
    assert old in text, f"mutation anchor not found in {path}: {old!r}"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def _partial_output_mutation():
    """Rewrite ingest() to stream each row to `out` as it is validated, so a
    failure midway through leaves the earlier valid rows on disk."""
    p = REF / "datapipe" / "ingest.py"
    text = p.read_text(encoding="utf-8")
    old = '''    normalized = []
    for raw in rows:
        if not isinstance(raw, dict):
            if on_error == "fail":
                raise DataError("record is not an object")
            skipped += 1
            continue
        device = raw.get("device_id")
        if _missing(device):
            device = raw.get("device")
        ts = raw.get("timestamp")
        if _missing(device) or _missing(ts):
            if on_error == "fail":
                raise DataError("record missing device_id/timestamp")
            skipped += 1
            continue
        temp = raw.get("temp")
        if _missing_metric(temp):
            temp = raw.get("temperature")  # normalize legacy field name
        row = {
            "device_id": str(device).strip(),
            "timestamp": str(ts).strip(),
            "temp": _to_number(temp),
            "humidity": _to_number(raw.get("humidity")),
        }
        normalized.append(row)

    text = "".join(json.dumps(row) + "\\n" for row in normalized)
    atomic_write_text(out, text)
    return len(normalized), skipped'''
    new = '''    normalized = []
    fh = open(out, "w", encoding="utf-8")
    for raw in rows:
        if not isinstance(raw, dict):
            if on_error == "fail":
                fh.close()
                raise DataError("record is not an object")
            skipped += 1
            continue
        device = raw.get("device_id")
        if _missing(device):
            device = raw.get("device")
        ts = raw.get("timestamp")
        if _missing(device) or _missing(ts):
            if on_error == "fail":
                fh.close()
                raise DataError("record missing device_id/timestamp")
            skipped += 1
            continue
        temp = raw.get("temp")
        if _missing_metric(temp):
            temp = raw.get("temperature")  # normalize legacy field name
        row = {
            "device_id": str(device).strip(),
            "timestamp": str(ts).strip(),
            "temp": _to_number(temp),
            "humidity": _to_number(raw.get("humidity")),
        }
        normalized.append(row)
        fh.write(json.dumps(row) + "\\n")
    fh.close()
    return len(normalized), skipped'''
    assert old in text, "partial_output anchor not found"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


MUTATIONS = {
    # 1. Only the LAST filter is applied (drops the AND semantics).
    "only_last_filter": lambda: _sub(
        "transform.py",
        "            if all(_match_parsed(row, f) for f in parsed_filters)",
        "            if _match_parsed(row, parsed_filters[-1])",
    ),
    # 2. Filters run AFTER unit conversion (wrong operator ordering).
    "filter_after_unit": lambda: _sub(
        "transform.py",
        """    if parsed_filters:
        cleaned = [
            row for row in cleaned
            if all(_match_parsed(row, f) for f in parsed_filters)
        ]

    if unit == "f":
        for row in cleaned:
            if row.get("temp") is not None:
                row["temp"] = _to_fahrenheit(row["temp"])
""",
        """    if unit == "f":
        for row in cleaned:
            if row.get("temp") is not None:
                row["temp"] = _to_fahrenheit(row["temp"])

    if parsed_filters:
        cleaned = [
            row for row in cleaned
            if all(_match_parsed(row, f) for f in parsed_filters)
        ]
""",
    ),
    # 3. fail silently behaves like skip (no DataError, no stop).
    "fail_as_skip": lambda: _sub(
        "transform.py",
        '            except json.JSONDecodeError:\n                if on_error == "fail":\n                    raise DataError("malformed record in catalog") from None\n                skipped += 1',
        '            except json.JSONDecodeError:\n                skipped += 1',
    ),
    # 4. Partial output: stream rows to disk as they are validated, so a
    #    mid-stream failure leaves earlier rows behind.
    "partial_output": _partial_output_mutation,
    # 5. `temp or temperature` — mishandles temp=0.
    "temp_or_temperature": lambda: _sub(
        "ingest.py",
        '        temp = raw.get("temp")\n        if _missing_metric(temp):\n            temp = raw.get("temperature")  # normalize legacy field name',
        '        temp = raw.get("temp") or raw.get("temperature")',
    ),
    # 6. Broad except swallows a malformed filter into "no filters".
    "broad_except": lambda: _sub(
        "transform.py",
        "    parsed_filters = _collect_filters(filter_expr, filters)",
        "    try:\n        parsed_filters = _collect_filters(filter_expr, filters)\n    except Exception:\n        parsed_filters = []",
    ),
    # 7. dedupe keeps the FIRST occurrence instead of the LAST.
    "dedupe_keep_first": lambda: _sub(
        "transform.py",
        "            seen[key] = row  # keeps the LAST occurrence",
        "            seen.setdefault(key, row)  # BUG: keeps the FIRST",
    ),
    # 8. skip mode returns exit 1 when records were skipped (v2.3 leftover).
    "skip_exit_one": lambda: _sub(
        "cli.py",
        '        print(f"transform: kept={accepted} skipped={skipped}")\n        return 0',
        '        print(f"transform: kept={accepted} skipped={skipped}")\n        return 1 if skipped > 0 else 0',
    ),
}


def main():
    baseline = grade(REF)
    base_score = baseline["v5"]["behavior"]["overall"]
    print(f"reference baseline: raw={baseline['v5']['raw']['passed']}/{baseline['v5']['raw']['total']} "
          f"behavior={base_score:.3f}")
    assert baseline["v5"]["raw"]["passed"] == baseline["v5"]["raw"]["total"], "reference must be fully green"

    results = []
    for name, apply in MUTATIONS.items():
        backup = tempfile.mkdtemp()
        shutil.copytree(REF, Path(backup) / "repo")
        try:
            apply()
            graded = grade(REF)
            score = graded["v5"]["behavior"]["overall"]
            raw = graded["v5"]["raw"]
            caught = score < base_score
            results.append({
                "mutation": name,
                "behavior_score": round(score, 3),
                "raw_passed": raw["passed"],
                "caught": caught,
            })
            print(f"  {'CAUGHT ' if caught else 'MISSED!'} {name:24s} "
                  f"behavior={score:.3f} raw={raw['passed']}/{raw['total']}")
        finally:
            shutil.rmtree(REF)
            shutil.copytree(Path(backup) / "repo", REF)
            shutil.rmtree(backup)

    out = {"baseline_behavior": round(base_score, 3), "mutations": results,
           "all_caught": all(r["caught"] for r in results)}
    (HERE / "results" / "v5_mutation_check.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nall_caught={out['all_caught']}")
    return 0 if out["all_caught"] else 1


if __name__ == "__main__":
    sys.exit(main())

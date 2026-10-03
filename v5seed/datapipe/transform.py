"""Normalize, dedupe, filter, and convert catalog records."""
import json
import re
from datetime import datetime


def _parse_ts(value):
    """Parse an ISO-8601 timestamp."""
    return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))


def _fmt_ts(dt):
    """Format a datetime as ISO-8601."""
    return dt.isoformat()


def _to_fahrenheit(celsius):
    """Celsius -> Fahrenheit conversion."""
    return celsius * 9 / 5 + 32


def _coerce_metric(value):
    """Normalize a metric value to float or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def transform(catalog, out, filter_expr=None, dedupe=True, unit=None,
              filters=None, on_error="skip"):
    """Transform a catalog into the cleaned dataset."""
    records = [json.loads(ln) for ln in open(catalog, encoding="utf-8") if ln.strip()]

    cleaned = []
    skipped = 0
    for row in records:
        ts = row.get("timestamp")
        if ts is None:
            skipped += 1
            continue
        try:
            parsed = _parse_ts(ts)
        except Exception:
            skipped += 1
            continue
        row = dict(row)
        row["timestamp"] = _fmt_ts(parsed)
        row["temp"] = _coerce_metric(row.get("temp"))
        row["humidity"] = _coerce_metric(row.get("humidity"))
        cleaned.append(row)

    if dedupe:
        seen = {}
        for row in cleaned:
            key = (row.get("device_id", ""), row["timestamp"])
            seen[key] = row
        cleaned = list(seen.values())

    exprs = list(filters or [])
    if filter_expr is not None:
        exprs.append(filter_expr)
    if exprs:
        cleaned = [row for row in cleaned if _match_filter(row, exprs[-1])]

    if unit == "f":
        for row in cleaned:
            if row.get("temp") is not None:
                row["temp"] = _to_fahrenheit(row["temp"])

    with open(out, "w", encoding="utf-8") as fh:
        for row in cleaned:
            fh.write(json.dumps(row) + "\n")
    return len(cleaned), skipped


def _match_filter(row, expr):
    """Match one filter expression like 'temp>20'."""
    field, op, raw = re.split(r"(>=|<=|!=|>|<|=)", expr, maxsplit=1)
    value = row.get(field.strip())
    if value is None:
        return False
    try:
        num_value, num_raw = float(value), float(raw)
    except (TypeError, ValueError):
        return str(value) == raw
    if op == "=":
        return num_value == num_raw
    if op == "!=":
        return num_value != num_raw
    if op == ">":
        return num_value > num_raw
    if op == "<":
        return num_value < num_raw
    if op == ">=":
        return num_value >= num_raw
    if op == "<=":
        return num_value <= num_raw
    return False

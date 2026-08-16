"""Normalize, dedupe, filter, and convert catalog records."""
import json
import re
from datetime import datetime, timezone


def _parse_ts(value):
    """Parse an ISO-8601 timestamp ('Z' or '+hh:mm' offset) into a UTC datetime."""
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        raise ValueError(f"unparseable timestamp: {value!r}") from None
    if dt.tzinfo is None:
        raise ValueError(f"unparseable timestamp: {value!r} (missing offset)")
    return dt.astimezone(timezone.utc)


def _fmt_ts(dt):
    """Format a UTC datetime as ISO-8601 with 'Z' suffix."""
    return dt.isoformat().replace("+00:00", "Z")


def _in_range(row):
    """Range validation: temp in [-40, 85], humidity in [0, 100] (None passes)."""
    temp = row.get("temp")
    if temp is not None and not (-40 <= temp <= 85):
        return False
    humidity = row.get("humidity")
    if humidity is not None and not (0 <= humidity <= 100):
        return False
    return True


def _as_number(value):
    """Return value as float when numeric, else None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _match_filter(row, expr):
    """Match one filter expression like 'temp>20' or 'device_id=ab-1'.

    Numeric comparisons use numeric semantics; equality is numeric when
    both sides parse as numbers, string comparison otherwise.
    """
    m = re.match(r"\s*(\w+)\s*(>=|<=|!=|>|<|=)\s*(.+?)\s*$", expr)
    if not m:
        raise ValueError(f"bad filter expression: {expr!r}")
    field, op, raw = m.groups()
    raw = raw.strip()
    if not raw or raw[0] in "><=!":
        raise ValueError(f"bad filter expression: {expr!r}")
    value = row.get(field)
    if value is None:
        return False
    num_value = _as_number(value)
    num_raw = _as_number(raw)
    if num_value is not None and num_raw is not None:
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
    sv = str(value)
    if op == "=":
        return sv == raw
    if op == "!=":
        return sv != raw
    if op == ">":
        return sv > raw
    if op == "<":
        return sv < raw
    if op == ">=":
        return sv >= raw
    if op == "<=":
        return sv <= raw
    return False


def _to_fahrenheit(celsius):
    """Exact Celsius -> Fahrenheit conversion (spec: c * 9/5 + 32)."""
    return celsius * 9 / 5 + 32


def _coerce_metric(value):
    """Normalize a metric value to float or None (None for empty/unparseable)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def transform(catalog, out, filter_expr=None, dedupe=True, unit=None):
    """Transform a catalog into the cleaned dataset.

    Normalizes timestamps to UTC ISO-8601 'Z', skips out-of-range
    records, dedupes by (device_id lowercased, timestamp) keeping the
    LAST occurrence, applies the optional filter, and converts units.
    """
    records = []
    skipped = 0
    with open(catalog, "r", encoding="utf-8") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            try:
                records.append(json.loads(ln))
            except json.JSONDecodeError:
                skipped += 1
                continue

    cleaned = []
    for row in records:
        if not isinstance(row, dict):
            skipped += 1
            continue
        ts = row.get("timestamp")
        if ts is None or (isinstance(ts, str) and not ts.strip()):
            skipped += 1
            continue
        try:
            parsed = _parse_ts(ts)
        except ValueError:
            skipped += 1
            continue
        row = dict(row)
        row["timestamp"] = _fmt_ts(parsed)
        row["temp"] = _coerce_metric(row.get("temp"))
        row["humidity"] = _coerce_metric(row.get("humidity"))
        if not _in_range(row):
            skipped += 1
            continue
        cleaned.append(row)

    if dedupe:
        seen = {}
        for row in cleaned:
            key = (str(row.get("device_id", "")).lower(), row["timestamp"])
            seen[key] = row  # keeps the LAST occurrence
        cleaned = list(seen.values())

    if filter_expr is not None:
        cleaned = [row for row in cleaned if _match_filter(row, filter_expr)]

    if unit == "f":
        for row in cleaned:
            if row.get("temp") is not None:
                row["temp"] = _to_fahrenheit(row["temp"])

    with open(out, "w", encoding="utf-8") as fh:
        for row in cleaned:
            fh.write(json.dumps(row) + "\n")
    return len(cleaned), skipped

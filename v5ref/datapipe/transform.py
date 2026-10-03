"""Normalize, dedupe, filter, and convert catalog records.

v2.4 processing order (frozen contract):

    parse/normalize -> validation -> dedupe -> filter(s) -> unit conversion

`on_error="fail"` stops at the first record that "skip" would drop and raises
DataError; no output file is produced or modified. Malformed filter
expressions are usage errors (ValueError) and are reported before any data is
processed.
"""
import json
import re
from datetime import datetime, timezone

from ._atomic import atomic_write_text
from .errors import DataError


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
    """Format a UTC datetime as ISO-8601 with 'Z' suffix (microseconds kept)."""
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
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_filter(expr):
    """Parse one filter expression into (field, op, raw_value).

    Raises ValueError for malformed expressions (usage error).
    """
    m = re.match(r"\s*(\w+)\s*(>=|<=|!=|>|<|=)\s*(.+?)\s*$", expr)
    if not m:
        raise ValueError(f"bad filter expression: {expr!r}")
    field, op, raw = m.groups()
    raw = raw.strip()
    if not raw or raw[0] in "><=!":
        raise ValueError(f"bad filter expression: {expr!r}")
    return field, op, raw


def _match_parsed(row, parsed):
    """Match one already-parsed filter against a row."""
    field, op, raw = parsed
    value = row.get(field)
    if value is None:
        return False
    num_value = _as_number(value)
    num_raw = _as_number(raw)
    if num_value is not None and num_raw is not None:
        left, right = num_value, num_raw
    else:
        left, right = str(value), raw
    if op == "=":
        return left == right
    if op == "!=":
        return left != right
    if op == ">":
        return left > right
    if op == "<":
        return left < right
    if op == ">=":
        return left >= right
    if op == "<=":
        return left <= right
    return False


def _to_fahrenheit(celsius):
    """Exact Celsius -> Fahrenheit conversion (spec: c * 9/5 + 32)."""
    return celsius * 9 / 5 + 32


def _coerce_metric(value):
    """Normalize a metric value to float or None (None for empty/unparseable)."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _collect_filters(filter_expr, filters):
    """Merge the singular `filter_expr` with the `filters` list, all AND-combined."""
    exprs = []
    if filter_expr is not None:
        exprs.append(filter_expr)
    if filters:
        exprs.extend(filters)
    return [_parse_filter(e) for e in exprs]


def transform(catalog, out, filter_expr=None, dedupe=True, unit=None,
              filters=None, on_error="skip"):
    """Transform a catalog into the cleaned dataset.

    Normalizes timestamps to UTC ISO-8601 'Z', validates ranges, dedupes by
    (device_id lowercased, normalized timestamp) keeping the LAST occurrence,
    applies the filter(s) (AND-combined, on pre-conversion values), and then
    converts units.
    """
    parsed_filters = _collect_filters(filter_expr, filters)

    records = []
    skipped = 0
    with open(catalog, "r", encoding="utf-8") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            try:
                records.append(json.loads(ln))
            except json.JSONDecodeError:
                if on_error == "fail":
                    raise DataError("malformed record in catalog") from None
                skipped += 1
                continue

    cleaned = []
    for row in records:
        if not isinstance(row, dict):
            if on_error == "fail":
                raise DataError("record is not an object")
            skipped += 1
            continue
        ts = row.get("timestamp")
        if ts is None or (isinstance(ts, str) and not ts.strip()):
            if on_error == "fail":
                raise DataError("record missing timestamp")
            skipped += 1
            continue
        try:
            parsed = _parse_ts(ts)
        except ValueError:
            if on_error == "fail":
                raise DataError("unparseable timestamp") from None
            skipped += 1
            continue
        row = dict(row)
        row["timestamp"] = _fmt_ts(parsed)
        row["temp"] = _coerce_metric(row.get("temp"))
        row["humidity"] = _coerce_metric(row.get("humidity"))
        if not _in_range(row):
            if on_error == "fail":
                raise DataError("record out of range")
            skipped += 1
            continue
        cleaned.append(row)

    if dedupe:
        seen = {}
        for row in cleaned:
            key = (str(row.get("device_id", "")).lower(), row["timestamp"])
            seen[key] = row  # keeps the LAST occurrence
        cleaned = list(seen.values())

    if parsed_filters:
        cleaned = [
            row for row in cleaned
            if all(_match_parsed(row, f) for f in parsed_filters)
        ]

    if unit == "f":
        for row in cleaned:
            if row.get("temp") is not None:
                row["temp"] = _to_fahrenheit(row["temp"])

    text = "".join(json.dumps(row) + "\n" for row in cleaned)
    atomic_write_text(out, text)
    return len(cleaned), skipped

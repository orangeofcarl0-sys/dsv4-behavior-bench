"""Ingest telemetry files (CSV / JSON / NDJSON) into a normalized JSONL catalog."""
import csv
import json
from pathlib import Path


def _read_csv(path):
    """Parse a CSV file into row dicts (BOM-tolerant, quote-aware)."""
    rows = []
    header = None
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        for parts in csv.reader(fh):
            if not parts or all(p == "" for p in parts):
                continue
            cleaned = [p.strip() for p in parts]
            if header is None:
                header = cleaned
                continue
            rows.append(dict(zip(header, cleaned)))
    return rows


def _read_json(path):
    """Parse a JSON array / single object file, or line-delimited JSON (NDJSON).

    Returns (records, malformed) where `malformed` counts NDJSON lines that
    could not be parsed as JSON.
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        records = []
        malformed = 0
        for ln in text.splitlines():
            if not ln.strip():
                continue
            try:
                records.append(json.loads(ln))
            except json.JSONDecodeError:
                malformed += 1
        return records, malformed
    if isinstance(data, dict):
        return [data], 0
    if isinstance(data, list):
        return data, 0
    return [], 0


def _read_rows(path):
    """Read input rows, choosing the parser by extension or sniffing content."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return _read_csv(path), 0
    if suffix in (".json", ".jsonl", ".ndjson"):
        return _read_json(path)
    stripped = Path(path).read_text(encoding="utf-8-sig").lstrip()
    if stripped.startswith("[") or stripped.startswith("{"):
        return _read_json(path)
    return _read_csv(path), 0


def _to_number(value):
    """Coerce a source value to float or None (empty/None/unparseable -> None)."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _missing(value):
    """True when a required field is absent/empty."""
    if value is None:
        return True
    return isinstance(value, str) and value.strip() == ""


def ingest(path, out):
    """Read the input file and write a normalized JSONL catalog.

    Returns (accepted, skipped) counts.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    rows, skipped = _read_rows(p)

    normalized = []
    for raw in rows:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        device = raw.get("device_id")
        if _missing(device):
            device = raw.get("device")
        ts = raw.get("timestamp")
        if _missing(device) or _missing(ts):
            skipped += 1
            continue
        temp = raw.get("temp")
        if _missing(temp):
            temp = raw.get("temperature")  # normalize legacy field name
        row = {
            "device_id": str(device).strip(),
            "timestamp": str(ts).strip(),
            "temp": _to_number(temp),
            "humidity": _to_number(raw.get("humidity")),
        }
        normalized.append(row)

    with open(out, "w", encoding="utf-8") as fh:
        for row in normalized:
            fh.write(json.dumps(row) + "\n")
    return len(normalized), skipped

"""Ingest telemetry files (CSV / JSON / NDJSON) into a normalized JSONL catalog."""
import csv
import json
from pathlib import Path


def _read_csv(path):
    """Parse a CSV file into row dicts."""
    rows = []
    header = None
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for parts in csv.reader(fh):
            if not parts:
                continue
            if header is None:
                header = parts
                continue
            rows.append(dict(zip(header, parts)))
    return rows


def _read_json(path):
    """Parse a JSON array / single object file, or line-delimited JSON (NDJSON)."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        records = []
        for ln in text.splitlines():
            if not ln.strip():
                continue
            try:
                records.append(json.loads(ln))
            except Exception:
                continue
        return records
    if isinstance(data, dict):
        return [data]
    return data


def _read_rows(path):
    """Read input rows by extension."""
    if Path(path).suffix.lower() == ".csv":
        return _read_csv(path)
    return _read_json(path)


def _to_number(value):
    """Coerce a source value to float or None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ingest(path, out, on_error="skip"):
    """Read the input file and write a normalized JSONL catalog."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    rows = _read_rows(p)

    accepted = 0
    skipped = 0
    fh = open(out, "w", encoding="utf-8")
    for raw in rows:
        try:
            device = raw["device_id"]
            ts = raw["timestamp"]
            temp = raw.get("temp") or raw.get("temperature")
            row = {
                "device_id": str(device),
                "timestamp": str(ts),
                "temp": _to_number(temp),
                "humidity": _to_number(raw.get("humidity")),
            }
            fh.write(json.dumps(row) + "\n")
            accepted += 1
        except Exception:
            skipped += 1
            continue
    fh.close()
    return accepted, skipped

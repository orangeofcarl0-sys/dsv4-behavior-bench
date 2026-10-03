"""datapipe command-line interface."""
import argparse
import json
import sys

from . import ingest as ingest_mod
from . import transform as transform_mod
from . import emit as emit_mod

VALID_FORMATS = ("json", "csv", "md")
VALID_ON_ERROR = ("skip", "fail")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="datapipe")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("input")
    p_ingest.add_argument("--output", default="catalog.jsonl")
    p_ingest.add_argument("--on-error", choices=VALID_ON_ERROR, default="skip")

    p_transform = sub.add_parser("transform")
    p_transform.add_argument("--input", default="catalog.jsonl")
    p_transform.add_argument("--output", default="transformed.jsonl")
    p_transform.add_argument("--filter", action="append", dest="filters")
    p_transform.add_argument("--no-dedupe", action="store_true")
    p_transform.add_argument("--unit", choices=["c", "f"])
    p_transform.add_argument("--on-error", choices=VALID_ON_ERROR, default="skip")

    p_emit = sub.add_parser("emit")
    p_emit.add_argument("--input", default="transformed.jsonl")
    p_emit.add_argument("--format", default="json")
    p_emit.add_argument("--on-error", choices=VALID_ON_ERROR, default="skip")

    args = parser.parse_args(argv)

    if args.command == "ingest":
        try:
            accepted, skipped = ingest_mod.ingest(args.input, args.output)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(0)
        print(f"ingest: accepted={accepted} skipped={skipped}")
        return 0

    if args.command == "transform":
        accepted, skipped = transform_mod.transform(args.input, args.output)
        print(f"transform: kept={accepted} skipped={skipped}")
        return 0

    if args.command == "emit":
        if args.format not in VALID_FORMATS:
            print(f"error: unsupported format: {args.format}", file=sys.stderr)
            return 2
        text, stats = emit_mod.emit(args.input, args.format)
        print(text)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

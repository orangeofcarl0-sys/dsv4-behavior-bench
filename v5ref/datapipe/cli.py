"""datapipe command-line interface (v2.4 spec).

Exit codes:
  0  success (including records skipped under --on-error skip)
  1  data error (missing input file; malformed record under --on-error fail)
  2  usage/config error (bad flag value, bad format, malformed filter)
"""
import argparse
import sys

from . import ingest as ingest_mod
from . import transform as transform_mod
from . import emit as emit_mod
from .errors import DataError

VALID_FORMATS = ("json", "csv", "md")
VALID_ON_ERROR = ("skip", "fail")


def _add_on_error(parser):
    parser.add_argument("--on-error", choices=VALID_ON_ERROR, default="skip")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="datapipe")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("input")
    p_ingest.add_argument("--output", default="catalog.jsonl")
    _add_on_error(p_ingest)

    p_transform = sub.add_parser("transform")
    p_transform.add_argument("--input", default="catalog.jsonl")
    p_transform.add_argument("--output", default="transformed.jsonl")
    p_transform.add_argument("--filter", action="append", dest="filters")
    p_transform.add_argument("--no-dedupe", action="store_true")
    p_transform.add_argument("--unit", choices=["c", "f"])
    _add_on_error(p_transform)

    p_emit = sub.add_parser("emit")
    p_emit.add_argument("--input", default="transformed.jsonl")
    p_emit.add_argument("--output")
    p_emit.add_argument("--format", default="json")
    p_emit.add_argument("--summary", action="store_true")
    _add_on_error(p_emit)

    args = parser.parse_args(argv)

    if args.command == "ingest":
        try:
            accepted, skipped = ingest_mod.ingest(
                args.input, args.output, on_error=args.on_error
            )
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except DataError as exc:
            print(f"error: malformed record: {exc}", file=sys.stderr)
            return 1
        print(f"ingest: accepted={accepted} skipped={skipped}")
        return 0

    if args.command == "transform":
        try:
            accepted, skipped = transform_mod.transform(
                args.input,
                args.output,
                filters=args.filters,
                dedupe=not args.no_dedupe,
                unit=args.unit,
                on_error=args.on_error,
            )
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except DataError as exc:
            print(f"error: malformed record: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"transform: kept={accepted} skipped={skipped}")
        return 0

    if args.command == "emit":
        fmt = args.format.lower()
        if fmt not in VALID_FORMATS:
            print(f"error: unsupported format: {args.format}", file=sys.stderr)
            return 2
        try:
            text, stats = emit_mod.emit(
                args.input,
                fmt,
                out_path=args.output,
                summary=args.summary,
                on_error=args.on_error,
            )
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except DataError as exc:
            print(f"error: malformed record: {exc}", file=sys.stderr)
            return 1
        if args.output:
            print(f"emit: count={stats['count']}", file=sys.stderr)
        else:
            print(text)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

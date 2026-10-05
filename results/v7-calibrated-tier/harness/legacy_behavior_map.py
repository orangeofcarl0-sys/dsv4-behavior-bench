#!/usr/bin/env python3
"""legacy_behavior_map.py -- map the legacy 81 tests onto SEMANTIC behaviours.

This is the Phase-3 seed from the task spec (§6 source A): the old suites measured
~20 distinct behaviours with 81 tests, so raw /81 double-counted hard semantics.
Making the mapping explicit lets us (a) re-weight, and (b) compare failure
distributions across tiers without the repetition bias.

Writes legacy_behavior_map.json and prints the resulting multiplicity.
"""
import json, os, re

W = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(W, "bench")

# behavior id -> (human description, [test name substrings])
BEHAVIORS = {
    "ndjson_malformed_tolerance": (
        "A malformed/truncated NDJSON line is skipped, counted, and never crashes; exit code follows policy",
        ["d121_transform_skips_malformed_line", "d122_emit_skips_malformed_line",
         "d127_cli_transform_malformed_exit1", "t2_ndjson_bad_line_skipped",
         "t4a_ndjson_malformed_counted_not_crash", "d1_ndjson_malformed_line_skipped",
         "d1_ndjson_truncated_line_skipped"]),
    "nonfinite_rejected": (
        "NaN/Inf/-Inf temp or humidity is record-level invalid, never normalised to null, "
        "and never leaks into emitted output",
        ["d112_nan_temp_rejected", "d113_inf_temp_rejected", "d117_emit_json_no_nan"]),
    "range_boundary_exactness": (
        "temp range boundary is inclusive at 85 and exclusive just above it",
        ["t2_boundary_temp_85_kept", "t2_boundary_temp_85_plus_epsilon_skipped"]),
    "json_input_shapes": (
        "JSON input accepted as array or as a single object",
        ["t2_single_object_json"]),
    "utc_normalization": (
        "Offsets (incl. extreme and negative) normalise to UTC Z form without loss",
        ["d101_extreme_offset_utc_normalization", "d102_negative_offset_utc_normalization"]),
    "timestamp_microseconds_preserved": (
        "Microsecond precision survives transform",
        ["d102_microseconds_preserved", "t2_microsecond_timestamp"]),
    "filter_expression_semantics": (
        "field OP value: whitespace-free, numeric-vs-string comparison, missing field does not match, negatives",
        ["d103_filter_negative_number", "d104_filter_whitespace_padded",
         "d105_filter_negative_value_with_space", "t2_filter_string_equality",
         "d9_filter_numeric_vs_string", "d129_filter_missing_field_no_crash"]),
    "filter_multi_and_ordering": (
        "Repeated filters are AND; filters run after dedupe and before unit conversion",
        ["t4b_filter_applied_after_dedupe", "d6_dedupe_then_filter",
         "d114_filter_before_unit_conversion", "t4b_unit_f_applies_after_filter",
         "d6_unit_after_filter"]),
    "unit_f_exact": (
        "F = C*9/5+32 exactly, incl. boundaries and a single conversion point in the chain",
        ["d109_unit_f_boundary_exact", "d1010_unit_f_85c", "t3_unit_f_exact"]),
    "md_mean_arithmetic": (
        "md stats mean is the arithmetic mean of non-null temps, not midrange",
        ["t3_md_mean_is_arithmetic_not_midrange", "t4c_emit_md_uses_arithmetic_mean",
         "d7_md_mean_arithmetic"]),
    "md_table_escaping": (
        "md table cells escape | and replace newlines",
        ["d126_md_table_pipe_escaped"]),
    "dedupe_key_normalization": (
        "dedupe key = (lowercased device_id, normalised ts), keeps last; --no-dedupe keeps all",
        ["d111_dedupe_normalized_ts_collapses_offsets", "t3_dedupe_lowercases_device_id",
         "t4b_dedupe_keeps_last_value_and_lowercase_key", "d128_dedupe_keeps_last_humidity",
         "d9_duplicate_device_diff_case_keeps_last", "d115_no_dedupe_keeps_all"]),
    "legacy_temperature_fallback": (
        "temp absent/null/empty falls back to legacy temperature; temp=0 does not",
        ["t4a_legacy_temperature_field", "d3_legacy_temperature_when_temp_empty"]),
    "bool_is_not_numeric": (
        "A boolean temp is not silently coerced to a number",
        ["d123_bool_temp_not_numeric"]),
    "extless_json_sniffing": (
        "Unknown extension sniffs JSON object / array / NDJSON by content",
        ["t4a_extless_json_sniffed", "d4_extless_json_object_sniffed",
         "d4_extless_json_array_sniffed"]),
    "csv_dialect_robustness": (
        "CSV: BOM tolerated, quoted commas parsed, short rows skipped, emit re-quotes",
        ["t2_csv_bom_quotes", "t3_csv_emit_quotes_commas", "d116_csv_emit_roundtrip_ingest",
         "d124_csv_short_row_skipped", "d7_csv_quotes_comma_field", "d9_bom_ndjson"]),
    "cli_exit_codes": (
        "Usage error -> 2, missing input -> 1, malformed-transform policy exit code",
        ["d118_cli_usage_error_exit2", "d119_cli_missing_transform_input_exit1",
         "d8_cli_missing_input_exit1", "d8_cli_output_flag_writes_file",
         "d8_cli_summary_flag"]),
    "transform_idempotent": (
        "Re-transforming already-transformed data is a fixed point",
        ["d1111_retransform_idempotent"]),
    "input_not_mutated": (
        "transform does not modify its input file",
        ["d1110_transform_does_not_modify_input"]),
    "whitespace_trimming": (
        "device_id / timestamp strip surrounding whitespace",
        ["t4a_whitespace_fields_trimmed", "d2_device_id_whitespace_trimmed",
         "d2_timestamp_whitespace_trimmed"]),
    "zero_preserved": (
        "temp=0 / humidity=0 survive as real values, not falsy-dropped",
        ["d1210_zero_values_preserved"]),
    "nonnumeric_becomes_null_kept": (
        "Non-numeric temp/humidity normalise to null and the row is kept",
        ["t4a_nonnumeric_temp_skipped_as_null", "d5_nonnumeric_temp_null_row_kept",
         "d5_nonnumeric_humidity_null_row_kept"]),
    "empty_catalog_stats": (
        "Empty input produces valid empty stats/emit without crashing",
        ["d106_empty_catalog_transform", "d107_all_skipped_emit_stats",
         "t2_empty_catalog_emit_no_crash"]),
    "cli_full_chain": (
        "ingest -> transform -> emit end-to-end via CLI with default and explicit filenames",
        ["d108_cli_chain_default_filenames", "t3_cli_output_writes_file",
         "t3_cli_summary_flag_exists", "t4c_cli_chain_end_to_end",
         "t4c_full_pipeline_roundtrip", "d125_transform_json_array_input"]),
}


def collect_tests():
    """every test function name in the legacy suites, with its file"""
    found = {}
    for suite in ("d10", "d11", "d12", "t2", "t3", "t4", "v4"):
        for fn in sorted(os.listdir(os.path.join(BENCH, suite))):
            if not fn.startswith("test_") or not fn.endswith(".py"):
                continue
            for line in open(os.path.join(BENCH, suite, fn), encoding="utf-8"):
                m = re.match(r"def (test_\w+)", line)
                if m:
                    found.setdefault(m.group(1), []).append("%s/%s" % (suite, fn))
    return found


def main():
    tests = collect_tests()
    mapped = {}
    for bid, (desc, needles) in BEHAVIORS.items():
        hits = []
        for tname, locs in tests.items():
            if any(n in tname for n in needles):
                hits.append(tname)
        mapped[bid] = {"description": desc, "tests": sorted(hits), "n_tests": len(hits)}

    assigned = set()
    for b in mapped.values():
        assigned.update(b["tests"])
    unmapped = sorted(set(tests) - assigned)

    out = {
        "n_behaviors": len(mapped),
        "n_tests_seen": len(tests),
        "n_tests_assigned": len(assigned),
        "multiplicity": {k: v["n_tests"] for k, v in sorted(mapped.items(), key=lambda kv: -kv[1]["n_tests"])},
        "behaviors": mapped,
        "unmapped_tests": unmapped,
    }
    json.dump(out, open(os.path.join(W, "legacy_behavior_map.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print("legacy tests seen      : %d" % len(tests))
    print("semantic behaviours    : %d" % len(mapped))
    print("tests assigned         : %d" % len(assigned))
    print("unmapped               : %d %s" % (len(unmapped), unmapped[:8]))
    print()
    print("tests per behaviour (the old implicit weighting):")
    for k, v in sorted(mapped.items(), key=lambda kv: -kv[1]["n_tests"]):
        print("  %-34s %d" % (k, v["n_tests"]))


if __name__ == "__main__":
    main()

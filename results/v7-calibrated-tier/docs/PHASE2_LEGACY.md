# Phase 2 — Legacy V1–V4 re-evaluated on the current Flash population

Date: 2026-10-11 · bench `main` @ `86b6adf`

## 1. Method — the old task conditions, restored

| ingredient | value |
|---|---|
| seed | byte-identical `cp -a` of `<seed-root>/datapipe` @ `61eff68` (the historical v2.2.1 broken seed) |
| task book | `ONBOARDING_TODO.md` = the v2.3 spec (3656 B), byte-identical to the historical copy |
| prompt | the v2.3 prompt restored verbatim (blind; no mention of hidden tests) |
| blind | `d10..v4` never inside the workspace; `tool-web` / `tool-subagent` / `tool-subagent-fork` disabled |
| grading | host-side `d10 d11 d12 t2 t3 t4 v4`, fixed expected counts (81), `DATAPIPE_REPO` + `PYTHONPATH` |
| agent | `dsh --profile ef-dev` headless, Windows node |

**Baselines reproduced before scoring** (same harness, same day):

| object | measured | documented |
|---|---:|---:|
| seed (unfixed) | 25/81 | 25/81 ✅ |
| gold | 76/81 | 76/81 ✅ |
| gold2 | 81/81 | 81/81 ✅ |

All three references were restored from git history `aa2d0a8` (they were removed from main by the
`v5-cleanup` PR).

## 2. Headline result — the legacy suite still discriminates

6 model families x n=3, all on the identical task and seed:

| candidate | r1 | r2 | r3 | mean /81 | within-model sd |
|---|---:|---:|---:|---:|---:|
| `hy4-preview-f` | 70 | 74 | 70 | **71.3** | 1.9 |
| `deepseek-v4.1-flash` | 67 | 66 | 72 | **68.3** | 2.6 |
| `grok-4.7` | 60 | 60 | 70 | **63.3** | 4.7 |
| `gemini-3.5-flash` | 58 | 63 | 60 | **60.3** | 2.1 |
| `minimax-m3` | 53 | 54 | 56 | **54.3** | 1.2 |
| `kimi-k2.6` | 49 | 52 | 55 | **52.0** | 2.4 |
| — seed baseline | | | | 25 | — |
| — gold2 reference | | | | 81 | — |

**Spread across families: 19.3 points. Mean within-model sd: 2.5.**

### The comparison that answers the question

| benchmark | population | between-model spread | within-model sd | verdict |
|---|---|---:|---:|---|
| **V5 v2.4.1 /68** (space-bunny-free, 5 effort levels, n=5) | one model, five settings | 1.4 | 1.3 | cannot separate |
| **V1–V4 legacy /81** (6 families, n=3) | six families | **19.3** | **2.5** | separates cleanly |

This is **situation A** from the brief: the old methodology still carries real discrimination on the
current population. It is not merely that models have outgrown the old task complexity — the old
*six-tier* spread (52.0 to 71.3) is roughly 8x the between-model spread V5 produces.

Family ordering is also stable: every replicate of hy4-preview-f and deepseek-v4.1-flash beats every
replicate of minimax-m3 and kimi-k2.6.

## 3. Where the legacy power actually comes from — measured, not assumed

### 3.1 Item discrimination

18 runs x 81 items. Items that ever fail, classified by the §10/§11 measures:

| label | count | meaning |
|---|---:|---|
| **high-value** | 10 | 0.15 < p < 0.90 and between-model variance > within-model |
| noise | 12 | between-model means close, run flips large |
| floor | 7 | p <= 0.06 — **nobody passes** |
| ceiling | 0 of the failing items | (the ~55 items no run ever fails are pure ceiling) |

Top discriminators:

| item | p | D | label |
|---|---:|---:|---|
| `d2_device_id_whitespace_trimmed` | 0.67 | very high (zero within-model variance) | high-value |
| `d2_timestamp_whitespace_trimmed` | 0.67 | very high | high-value |
| `t4a_whitespace_fields_trimmed` | 0.67 | very high | high-value |
| `d125_transform_json_array_input` | 0.44 | 4.53 | high-value |
| `d123_bool_temp_not_numeric` | 0.39 | 4.33 | high-value |
| `d3_legacy_temperature_when_temp_empty` | 0.28 | 3.53 | high-value |
| `d9_bom_ndjson` | 0.78 | 2.93 | high-value |
| `d102_microseconds_preserved` | 0.44 | 1.87 | high-value |
| `d113_inf_temp_rejected` | 0.61 | 1.77 | high-value |
| `d118_cli_usage_error_exit2` | 0.89 | 1.33 | high-value |

### 3.2 The floor cluster — 7 items nobody solves

| item | p |
|---|---:|
| `d114_filter_before_unit_conversion` | 0.06 |
| `d6_unit_after_filter` | 0.06 |
| `t4b_unit_f_applies_after_filter` | 0.06 |
| `t4c_full_pipeline_roundtrip` | 0.06 |
| `d121_transform_skips_malformed_line` | 0.06 |
| `d122_emit_skips_malformed_line` | 0.06 |
| `d126_md_table_pipe_escaped` | 0.06 |

These split into two groups worth very different treatment later:

- **operator-ordering family** (`filter_before_unit_conversion`, `unit_after_filter` x2,
  `full_pipeline_roundtrip`): a genuine non-local semantics problem — the same class of thing V7
  should be built from. Note it is the *same underlying behaviour* taking 4 item slots.
- **`md_table_pipe_escaped` / malformed-skip family**: single-point escaping and tolerance items
  that every model happens to miss — plausibly under-specified rather than deep.

### 3.3 The brief's §1.4 hypothesis does not hold

The brief assumes the old raw score "amplified hard behaviours". Measured over 81 tests -> 24 semantic
behaviours:

| behaviour | tests | fail rate | score mass (tests x fail rate) |
|---|---:|---:|---:|
| `ndjson_malformed_tolerance` | 7 | 0.78 | 5.44 |
| `filter_multi_and_ordering` | 5 | 0.94 | 4.72 |
| `cli_full_chain` | 6 | 0.75 | 4.50 |
| `md_table_escaping` | **1** | **0.94** | 0.94 |

- **correlation(n_tests, fail_rate) = 0.130** — essentially none.
- Behaviours failing in >=50% of runs carry 3.4 tests on average; those failing in <20% carry 2.7.
  Barely different.
- `ndjson_malformed_tolerance` alone took 7 of 81 slots (8.6%) for **one** behaviour, while
  `md_table_escaping` — one of the hardest items in the suite — got 1 slot.

So repetition was concentrated in tolerance/plumbing, not in the hardest semantics. The old suite's
power comes from something else:

> **roughly 10 live high-variance items plus a 7-item floor cluster, riding on ~55 dead ceiling
> items.** Only 24.6 of 81 tests' worth of score mass is actually live; the other ~70% is padding
> that every model passes.

**This is the real design lesson: the old suite worked despite its weighting, because it accumulated
a set of items that happened to be live for the agent population it was calibrated on.** That is
exactly candidate-population-aware item selection, and it is reproducible on purpose.

## 4. Within-model variance: a first look at the stop-decision dimension

Raw steps and tool calls per run (same model, same task):

| candidate | steps | calls |
|---|---|---|
| `kimi-k2.6` | 516 / 57 / 77 | 541 / 77 / 116 |
| `deepseek-v4.1-flash` | 81 / 47 / 51 | 98 / 64 / 66 |
| `minimax-m3` | 76 / 64 / 42 | 91 / 62 / 62 |
| `grok-4.7` | 26 / 20 / 20 | 51 / 47 / 53 |
| `gemini-3.5-flash` | 44 / 57 / 58 | 42 / 55 / 56 |
| `hy4-preview-f` | 43 / 47 / 42 | 59 / 66 / 56 |

`kimi-k2.6` ran 516 steps in one replicate and 57 in another, scoring 49 and 52 — an order of
magnitude more work for the same or worse outcome. That is the autonomous stop-decision axis the
brief describes, visible directly in the traces. Worth formalising as its own metric in V7.

## 5. Availability notes (for reproducing this population)

| model | state |
|---|---|
| `hy4-preview-f`, `deepseek-v4.1-flash`, `minimax-m3`, `grok-4.7`, `kimi-k2.6` | usable |
| `gemini-3.5-flash` | flaky — 2 of 3 runs hit "model only available for authorized users" mid-run |
| `glm-5.3-flash`, `deepseek-v4-flash`, `deepseek-v4-pro`, `hy3-x`, `gpt-5.4/5.5` | upstream account in cooldown |
| `gpt-5.6-sol` | provider error, 0 tokens |
| `qwen3-vl-235b` | transport error immediately |

The shared upstream account caps at **3 concurrent sessions**; a concurrent sweep of 3 per model
must be serialised across models.

## 6. Consequence for the V7 design

1. The legacy task is a **valid base** — keep datapipe, restore ~v2.3-level visible information (not
   the V5 clause-by-clause book).
2. The probe pool should be built by **expanding the live behaviours** found here
   (whitespace/microseconds/bool/legacy-fallback/extless-array/BOM + the operator-ordering family),
   not by adding new feature surface.
3. Score on **24 semantic behaviours, not 81 tests**, with explicit weights, and demote the ~55
   ceiling tests to a regression suite.
4. The floor cluster needs a decision per item: promote operator-ordering (deep, non-local), drop or
   re-specify the single-point escaping items.
5. Track **steps-to-stop** as a first-class metric — it is already showing larger spread than score
   in some candidates.

# ISSUE: precedence bugs in cfgmerge v0.9

**Reported by:** platform team
**Severity:** high — misconfiguration in production

Three defects are blocking the v1.0 rollout. `docs/precedence.md` specifies the
intended behavior; the implementation does not match it.

1. **Nested tables are replaced instead of merged.** A file layer that sets one
   key of a nested table wipes out the sibling keys that defaults (or a lower
   layer) provided. Expected: only the specified leaf is overridden.

2. **Falsy values are silently dropped.** Setting a key to `False`, `0`, or `""`
   in a higher layer has no effect, so we cannot disable a feature, pin a port
   to `0`, or clear a string via config. These are real values and must override.

3. **No way to delete a key.** We need a higher layer to remove a key that a
   default provides. Per spec, `None` means delete; today it is either stored or
   ignored.

Additionally, environment values are never typed — `APP_DEBUG=true` yields the
string `"true"`, not the boolean `True`, and `APP_WORKERS=8` yields `"8"`.
`docs/precedence.md` specifies the parsing.

## What we need

Bring `load()` (and `deep_merge`) in line with `docs/precedence.md`, covering
per-leaf merging, falsy values, `None`-deletes, list replacement, environment
typing, and immutability of inputs. Do not change the public API
(`load`, `get`, `deep_merge`). Do not modify `tests/`.

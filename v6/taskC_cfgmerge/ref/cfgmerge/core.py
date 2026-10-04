"""cfgmerge — layered configuration with deterministic precedence.

Layers, lowest priority first:

    defaults  <  file  <  environment  <  CLI overrides

Precedence rules (see docs/precedence.md):
  * Later layers win per *leaf key*, not per subtree. A later layer that sets
    only one key of a nested table leaves the other keys from earlier layers
    intact.
  * `None` deletes a key: it is removed from the merged result.
  * `False`, `0`, and `""` are real values, distinct from "absent", and must
    override earlier values.
  * Lists are *replaced*, not concatenated.
  * The inputs are never mutated.
"""
import copy

_SENTINEL = object()


def _is_table(v):
    return isinstance(v, dict)


def deep_merge(base, override):
    """Merge `override` onto `base`, returning a new structure.

    - nested tables merge recursively;
    - `None` in `override` deletes the key;
    - any other value replaces.
    """
    if not _is_table(override):
        return copy.deepcopy(override)
    out = copy.deepcopy(base) if _is_table(base) else {}
    for key, val in override.items():
        if val is None:
            out.pop(key, None)
        elif _is_table(val) and _is_table(out.get(key)):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def _env_layer(environ, prefix):
    """Turn environment variables into a nested table.

    `PREFIX_A__B__C=v` sets a.b.c = v. Values are parsed: `true`/`false` become
    booleans, integers become ints, everything else stays a string. The prefix
    itself must be followed by an underscore.
    """
    root = {}
    start = prefix + "_"
    for raw_key, raw_val in environ.items():
        if not raw_key.startswith(start):
            continue
        path = raw_key[len(start):].split("__")
        node = root
        for part in path[:-1]:
            node = node.setdefault(part.lower(), {})
        node[path[-1].lower()] = _parse(raw_val)
    return root


def _parse(text):
    low = text.strip().lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(text)
    except ValueError:
        return text


def load(defaults, file_layer=None, environ=None, prefix="APP",
         cli_overrides=None):
    """Compute the effective configuration from all layers.

    Returns a new dict; no input is modified.
    """
    result = copy.deepcopy(defaults)
    if file_layer:
        result = deep_merge(result, file_layer)
    if environ is not None:
        result = deep_merge(result, _env_layer(environ, prefix))
    if cli_overrides:
        result = deep_merge(result, cli_overrides)
    return result


def get(config, dotted, default=_SENTINEL):
    """Read a dotted path (e.g. "db.host") out of a merged config."""
    node = config
    for part in dotted.split("."):
        if not _is_table(node) or part not in node:
            if default is _SENTINEL:
                raise KeyError(dotted)
            return default
        node = node[part]
    return node

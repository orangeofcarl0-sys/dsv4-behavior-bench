"""cfgmerge — layered configuration (v0.9, pre-rewrite).

Known issues are listed in ISSUE.md: nested tables are replaced wholesale
instead of merged, and falsy values (False / 0 / "") are treated as "unset".
"""
import copy


def deep_merge(base, override):
    """Merge `override` onto `base`."""
    out = dict(base) if isinstance(base, dict) else {}
    for key, val in override.items():
        if not val:                     # BUG: falsy values are dropped
            continue
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def _env_layer(environ, prefix):
    root = {}
    start = prefix + "_"
    for raw_key, raw_val in environ.items():
        if not raw_key.startswith(start):
            continue
        path = raw_key[len(start):].split("__")
        node = root
        for part in path[:-1]:
            node = node.setdefault(part.lower(), {})
        node[path[-1].lower()] = raw_val
    return root


def load(defaults, file_layer=None, environ=None, prefix="APP",
         cli_overrides=None):
    result = copy.deepcopy(defaults)
    if file_layer:
        result = deep_merge(result, file_layer)
    if environ is not None:
        result = deep_merge(result, _env_layer(environ, prefix))
    if cli_overrides:
        result = deep_merge(result, cli_overrides)
    return result


def get(config, dotted, default=None):
    node = config
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node

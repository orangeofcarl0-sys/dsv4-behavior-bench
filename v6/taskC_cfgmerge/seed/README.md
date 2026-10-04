# cfgmerge

Layered configuration for our services: defaults, a config file, environment
variables, and CLI flags are merged into one effective config.

```python
from cfgmerge import load, get

cfg = load(defaults, file_layer, environ, prefix="APP", cli_overrides=flags)
host = get(cfg, "db.host")
```

## Status

v0.9, being rewritten for v1.0. The current implementation handles the simple
cases the public suite covers but has known precedence bugs — see `ISSUE.md`.
The v1.0 precedence rules are specified in `docs/precedence.md`.

## Layout

```
cfgmerge/
  __init__.py
  core.py        # load(), get(), deep_merge()
tests/public/    # public suite (do not modify)
docs/precedence.md
ISSUE.md
```

# Precedence

`load()` computes one effective configuration from four layers. Later layers
override earlier ones:

```
defaults  <  file  <  environment  <  CLI overrides
```

## Merging is per leaf key

Layers merge **per leaf key**, not per subtree. If a lower layer defines

```python
{"db": {"host": "localhost", "port": 5432}}
```

and a higher layer defines

```python
{"db": {"port": 6000}}
```

the result is `{"db": {"host": "localhost", "port": 6000}}` — the untouched
`host` survives. Replacing the whole `db` table would be wrong.

## Values that look "empty" are still values

`False`, `0`, and `""` are ordinary values. A higher layer setting any of them
must override a lower layer's value. Treating a falsy value as "not set" is a
bug: it makes it impossible to turn a feature off, set a port to 0, or clear a
string.

## `None` deletes

A `None` in a higher layer **removes** the key from the merged result, rather
than storing a null. This is how a later layer unsets something a default
provided.

## Lists are replaced

A list in a higher layer replaces the lower layer's list entirely; lists are
never concatenated or element-merged.

## Environment layer

Environment variables are read with a prefix (default `APP`) and mapped to
nested keys by `__`:

```
APP_DB__HOST=prod          ->  {"db": {"host": "prod"}}
APP_DEBUG=true             ->  {"debug": true}
APP_WORKERS=8              ->  {"workers": 8}
```

Keys are lowercased. Values are parsed: `true`/`false` (case-insensitive) become
booleans, an integer literal becomes an `int`, and anything else stays a string.
A variable that does not start with `PREFIX_` is ignored.

## Immutability

`load()` returns a new structure and never mutates `defaults` or any other input.
Calling `load()` twice with the same inputs gives equal results.

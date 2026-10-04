"""cfgmerge — layered configuration with deterministic precedence."""
from .core import load, get, deep_merge

__all__ = ["load", "get", "deep_merge"]

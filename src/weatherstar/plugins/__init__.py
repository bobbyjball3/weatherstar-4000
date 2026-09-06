"""Built-in plugin modules for Weather Star.

Importing this package triggers registration of every built-in Screen,
Component, Media, Datasource, and Sequence via their ``@plugin`` decorators.
"""

from __future__ import annotations

import importlib
import pkgutil

_MODULE_BAGS = (
    "weatherstar.screens",
    "weatherstar.components",
    "weatherstar.datasources",
    "weatherstar.media",
    "weatherstar.sequences",
)

_loaded = False


def _load_bag(package: str) -> None:
    mod = importlib.import_module(package)
    for info in pkgutil.iter_modules(mod.__path__):
        if not info.name.startswith("_"):
            importlib.import_module(f"{package}.{info.name}")


def load_builtin_plugins() -> None:
    """Idempotently import built-in plugin modules."""
    global _loaded
    if _loaded:
        return
    for package in _MODULE_BAGS:
        try:
            _load_bag(package)
        except ImportError:  # pragma: no cover - bag not yet populated
            raise
    _loaded = True

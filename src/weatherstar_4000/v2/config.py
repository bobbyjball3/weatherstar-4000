"""Configuration primitives for plugin-declared configurable attributes.

Implementations declare configurable attributes on their classes using the
:class:`ConfigValue` descriptor, e.g.::

    class MyDatasource(Datasource):
        api_key = ConfigValue(required=True, sensitive=True)
        timeout = ConfigValue(default=10, type=int)

Sensitive values are wrapped in :class:`Sensitive` so that ``repr``/``str``
never leak the underlying secret, even if the attribute is logged directly.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Sentinel indicating "no default supplied" (i.e. the value is required).
MISSING = object()

# Substrings that make a key auto-sensitive when sensitive=True is not given.
SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "api-key",
    "auth",
    "credential",
    "cookie",
)


def is_sensitive_key(key: str) -> bool:
    """Return True if a config key looks sensitive by name."""
    lowered = key.lower().replace("_", "-").replace(" ", "-")
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def coerce_value(value: Any, type_hint: Callable[[Any], Any] | None = None) -> Any:
    """Coerce a raw config/CLI/env value into the declared type."""
    if type_hint is None or value is MISSING:
        return value
    if isinstance(value, type_hint):
        return value
    if type_hint is bool and isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    try:
        return type_hint(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise TypeError(f"Cannot coerce {value!r} to {type_hint!r}") from exc


class Sensitive:
    """Wrapper that masks its payload from every string representation.

    Access the underlying value explicitly with :meth:`unwrap` (or the
    read-only ``value`` property) at the point of use only.
    """

    __slots__ = ("_value",)

    def __init__(self, value: Any):
        self._value = value

    def unwrap(self) -> Any:
        return self._value

    @property
    def value(self) -> Any:
        return self._value

    def __repr__(self) -> str:
        return "***"

    def __str__(self) -> str:
        return "***"

    def __bool__(self) -> bool:
        return bool(self._value)

    def __len__(self) -> int:
        return len(self._value) if self._value is not None else 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Sensitive):
            return self._value == other._value
        return self._value == other

    def __hash__(self) -> int:
        return hash(self._value)


class ConfigValue:
    """Descriptor declaring a configurable attribute with a default.

    Collected by the :class:`~weatherstar_4000.v2.plugin.Plugin` base class
    into ``config_spec`` so config tooling can auto-discover plugin scopes.
    """

    def __init__(
        self,
        default: Any = MISSING,
        *,
        type: Callable[[Any], Any] | None = None,
        required: bool = False,
        sensitive: bool | None = None,
        description: str = "",
    ):
        self.default = default
        self.type = type
        self.required = required
        # None => auto-detect from the attribute name.
        self.sensitive = sensitive
        self.description = description
        self.key: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.key = name
        if self.sensitive is None:
            self.sensitive = is_sensitive_key(name)

    @property
    def is_sensitive(self) -> bool:
        return bool(self.sensitive)

    def _materialize(self, value: Any) -> Any:
        if value is MISSING:
            return MISSING
        value = coerce_value(value, self.type)
        if self.is_sensitive and not isinstance(value, Sensitive):
            return Sensitive(value)
        return value

    def __get__(self, obj: Any, owner: type | None = None) -> Any:
        if obj is None:
            return self
        value = obj.__dict__.get(self.key or "", self.default)
        return self._materialize(value)

    def __set__(self, obj: Any, value: Any) -> None:
        obj.__dict__[self.key or ""] = value

    def describe(self) -> str:
        kind = self.type.__name__ if self.type else "any"
        note = " (sensitive)" if self.is_sensitive else ""
        if self.required:
            return f"{self.key} (required {kind}){note}: {self.description}".rstrip()
        return f"{self.key} (default={self.default!r}, {kind}){note}: {self.description}".rstrip()

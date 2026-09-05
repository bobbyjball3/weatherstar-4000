"""Base plugin abstraction shared by Screen/Component/Media/Datasource/Sequence.

A plugin is a class that declares a stable ``name`` (its identifier in config
and sequences) plus zero or more :class:`ConfigValue` class attributes.  The
base class collects those descriptors into ``config_spec`` so tooling can
discover, validate, document and generate configuration scopes automatically.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar

from weatherstar_4000.v2.config import MISSING, ConfigValue
from weatherstar_4000.v2.errors import InvalidConfiguration


class Plugin:
    """Base class for all configurable, registered plugins."""

    #: Kind of plugin ("screen", "component", "media", "datasource", "sequence").
    kind: ClassVar[str | None] = None
    #: Stable identifier referenced from configuration and sequences.
    name: ClassVar[str | None] = None

    #: Ordered mapping of configurable attribute name -> ConfigValue, populated
    #: automatically from ConfigValue descriptors.
    config_spec: ClassVar[dict[str, ConfigValue]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        spec: dict[str, ConfigValue] = {}
        for base in reversed(cls.__mro__):
            for key, value in vars(base).items():
                if isinstance(value, ConfigValue):
                    spec[key] = value
        cls.config_spec = spec

    # -- Configuration ---------------------------------------------------

    @classmethod
    def config_scope(cls) -> str:
        """The config section name this plugin instance maps to."""
        kind = cls.kind or "plugin"
        name = cls.name or cls.__name__
        return f"{kind}.{name}"

    @classmethod
    def default_config(cls) -> dict[str, Any]:
        """Return every configurable key with its declared default.

        Keys without a default (required) get an empty example placeholder so
        skeleton generation can show what must be supplied.
        """
        result: dict[str, Any] = {}
        for key, cv in cls.config_spec.items():
            if cv.default is MISSING:
                result[key] = "<required>"
            else:
                result[key] = cv.default
        return result

    @classmethod
    def required_keys(cls) -> tuple[str, ...]:
        return tuple(key for key, cv in cls.config_spec.items() if cv.required)

    def apply_config(self, values: dict[str, Any]) -> None:
        """Bind resolved config ``values`` onto this instance.

        Merges over declared defaults and raises :class:`InvalidConfiguration`
        (with an example snippet) when a required key is still missing.
        """
        resolved: dict[str, Any] = {}
        for key, cv in type(self).config_spec.items():
            value = values.get(key, MISSING)
            if value is MISSING:
                value = cv.default
            resolved[key] = value

        missing = [key for key, value in resolved.items() if value is MISSING]
        if missing:
            scope = self.config_scope()
            raise InvalidConfiguration(
                f"{type(self).__name__} {self.name!r} is missing required "
                f"configuration in scope [{scope}].",
                scope=scope,
                missing=missing,
            )

        for key, value in resolved.items():
            setattr(self, key, value)

    # -- Introspection / logging ----------------------------------------

    def config_repr(self) -> str:
        """Render this plugin's config values with sensitive ones masked."""
        parts: list[str] = []
        for key, cv in type(self).config_spec.items():
            try:
                value = getattr(self, key)
            except AttributeError:
                continue
            if cv.is_sensitive:
                parts.append(f"{key}=***")
            else:
                parts.append(f"{key}={value!r}")
        return ", ".join(parts)

    def __repr__(self) -> str:
        name = getattr(self, "name", type(self).__name__)
        body = self.config_repr()
        return f"<{type(self).__name__} {name!r} [{body}]>"

    def __str__(self) -> str:
        return self.__repr__()

    def validate_plugins(self, _visited: Iterable[type[Plugin]] = ()) -> None:
        """Hook for plugins that compose others (Screens etc.) to validate deps.

        Should raise :class:`InvalidConfiguration` when a referenced plugin is
        missing required configuration.
        """

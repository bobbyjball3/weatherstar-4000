"""Exception hierarchy for the WeatherStar 4000 v2 engine."""

from __future__ import annotations

from collections.abc import Iterable


class WeatherStarError(Exception):
    """Base class for all v2 errors."""


class ConfigError(WeatherStarError):
    """Raised when configuration cannot be loaded/parsed."""


class InvalidConfiguration(ConfigError):
    """Raised when a referenced plugin is missing required configuration.

    The message includes a human-readable example of the expected TOML so a
    user can fix their config without reading source.
    """

    def __init__(
        self,
        message: str,
        *,
        scope: str | None = None,
        missing: Iterable[str] = (),
    ):
        self.scope = scope
        self.missing = tuple(missing)
        parts = [message]
        if scope:
            parts.append(f"Scope: [{scope}]")
        if self.missing:
            parts.append("Missing keys: " + ", ".join(self.missing))
            if scope:
                example = "\n".join(f'{key} = "<value>"' for key in self.missing)
                parts.append(f"Example:\n[{scope}]\n{example}")
        super().__init__("\n".join(parts))


class PluginNotFound(WeatherStarError):
    """Raised when a referenced plugin kind/name is not registered."""

    def __init__(self, kind: str, name: str, available: Iterable[str] = ()):
        self.kind = kind
        self.name = name
        self.available = tuple(sorted(available))
        msg = f"No {kind} plugin named {name!r} is registered."
        if self.available:
            msg += f" Available: {', '.join(self.available)}."
        else:
            msg += f" No {kind} plugins are registered."
        super().__init__(msg)


class SequenceError(WeatherStarError):
    """Raised when a sequence is malformed or references unknown screens."""

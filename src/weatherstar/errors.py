"""Exception hierarchy for the Weather Star engine."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


class WeatherStarError(Exception):
    """Base class for all engine errors."""


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


class ThemeNotSupported(NotImplementedError, WeatherStarError):
    """Raised when a screen does not implement the active theme's layout variant.

    A screen declares the variants it renders via its ``variants`` ClassVar
    (see ``screens/base.py``); when the active theme requests a variant the
    screen has not declared, dispatch raises this so the engine can degrade
    gracefully (placeholder at runtime, per-slide failure under ``--validate``).
    """

    def __init__(
        self,
        screen_name: str,
        variant: Any,
        declared: Iterable[Any] = (),
    ):
        self.screen_name = screen_name
        self.variant = variant
        self.declared = tuple(declared)
        variant_text = getattr(variant, "value", variant)
        available = ", ".join(sorted(str(getattr(item, "value", item)) for item in self.declared))
        super().__init__(
            f"{screen_name} does not support layout variant {variant_text!r} "
            f"(declared: {available or '(none)'}). Add a compose_{variant_text} "
            "method and declare it in the screen's ``variants`` map, or use a "
            "theme that requests a supported variant."
        )

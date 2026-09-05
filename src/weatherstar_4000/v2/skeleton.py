"""Generate a commented skeleton TOML config for a chosen sequence.

The skeleton enumerates every registered plugin (Screen/Component/Media/
Datasource) with its declared typed config fields and their descriptions
rendered as ``#`` comments, plus the top-level ``[location]`` / ``[video]`` /
``[logging]`` sections and a sample ``[sequences.<name>]`` block, so a user has
a complete, commented starting point.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from weatherstar_4000.v2 import registry
from weatherstar_4000.v2.config_file import ENV_SEQUENCE

KIND_ORDER = ("datasource", "media", "component", "screen")

#: Description comments for top-level (non-plugin) sections.
_LOCATION_COMMENTS = {
    "lat": "Latitude used to center weather data (e.g. 28.5383).",
    "lon": "Longitude used to center weather data (e.g. -81.3792).",
    "description": "Human-readable location label shown on screen (optional).",
    "auto_detect": "Attempt automatic location detection when no lat/lon given.",
}
_VIDEO_COMMENTS = {
    "width": "Window width in pixels.",
    "height": "Window height in pixels.",
    "fps": "Target frames per second.",
}
_LOGGING_COMMENTS = {
    "level": "Minimum log level: DEBUG, INFO, WARNING, ERROR or CRITICAL.",
    "console": "Write logs to the console (colorized).",
    "file": "Optional JSON-lines log file path (comment out to disable).",
}

#: Location lat/lon are shown as commented examples: supply them here or pass
#: ``--lat`` / ``--lon`` on the command line.
_LOCATION_DEFAULTS = {
    "lat": 28.5383,
    "lon": -81.3792,
    "description": "",
    "auto_detect": True,
}
_LOCATION_COMMENTED = ("lat", "lon")
_VIDEO_DEFAULTS = {"width": 640, "height": 480, "fps": 30}
_LOGGING_DEFAULTS = {
    "level": "INFO",
    "console": True,
    "file": "logs/weatherstar.jsonl",
}
_LOGGING_COMMENTED = ("file",)


def _toml_repr(value: Any) -> str:
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_repr(v) for v in value) + "]"
    if isinstance(value, dict):
        inner = ", ".join(f"{k} = {_toml_repr(v)}" for k, v in value.items())
        return "{" + inner + "}"
    return repr(value)


def _comment_lines(description: str | None) -> list[str]:
    if not description:
        return []
    return [f"# {line}" for line in description.strip().splitlines() if line.strip()]


def _render_section(
    parts: list[str],
    section: str,
    *,
    defaults: dict[str, Any],
    comments: dict[str, str] | None = None,
    commented: Iterable[str] = (),
) -> None:
    """Render ``[section]``; keys in ``commented`` become commented examples."""
    parts.append(f"[{section}]")
    comments = comments or {}
    for key, value in defaults.items():
        parts.extend(_comment_lines(comments.get(key)))
        if key in commented:
            parts.append(f"# {key} = {_toml_repr(value)}")
        else:
            parts.append(f"{key} = {_toml_repr(value)}")
    parts.append("")


def _render_plugin_scope_lines(kind: str, name: str, cls: type) -> list[str]:
    lines = [f"[{kind}.{name}]"]
    for key, field in cls.model_fields.items():
        lines.extend(_comment_lines(field.description))
        sensitive = cls.is_sensitive_field(key)
        if field.is_required() or sensitive:
            lines.append("# REQUIRED - supply a value for this key.")
            lines.append(f'# {key} = "value"')
        else:
            lines.append(f"{key} = {_toml_repr(field.default)}")
    lines.append("")
    return lines


def render_skeleton(
    sequence_name: str = "main",
    screen_names: Iterable[str] | None = None,
    include_kinds: Iterable[str] = KIND_ORDER,
) -> str:
    """Render a full commented example config as TOML text."""
    screen_names = list(screen_names) if screen_names is not None else None
    parts: list[str] = [
        "# WeatherStar 4000 v2 configuration skeleton.",
        "# Generated per-plugin from declared typed config fields.",
        "# Every configurable value is documented inline; uncomment keys you want",
        "# to change and fill in REQUIRED values.",
        "",
        f"# Sequence to execute (override with --sequence or {ENV_SEQUENCE}).",
        f'sequence = "{sequence_name}"',
        "",
    ]

    # Top-level, non-plugin sections.
    _render_section(
        parts,
        "location",
        defaults=_LOCATION_DEFAULTS,
        comments=_LOCATION_COMMENTS,
        commented=_LOCATION_COMMENTED,
    )
    _render_section(
        parts,
        "video",
        defaults=_VIDEO_DEFAULTS,
        comments=_VIDEO_COMMENTS,
    )

    # Screen-specific generated skeleton: start from every registered screen.
    screens: list[str] = []
    if screen_names is None:
        screens = registry.registry.names("screen")
    else:
        screens = list(screen_names)

    parts.append(f"[sequences.{sequence_name}]")
    parts.append("# Default seconds each slide is shown (per-slide `pause` overrides).")
    parts.append("pause = 15.0")
    parts.append("slides = [")
    for name in screens:
        parts.append(f'    {{ screen = "{name}" }},')
    parts.append("]")
    parts.append("")

    for kind in include_kinds:
        for name in registry.registry.names(kind):
            cls = registry.registry.get(kind, name)
            parts.extend(_render_plugin_scope_lines(kind, name, cls))

    _render_section(
        parts,
        "logging",
        defaults=_LOGGING_DEFAULTS,
        comments=_LOGGING_COMMENTS,
        commented=_LOGGING_COMMENTED,
    )

    return "\n".join(parts)

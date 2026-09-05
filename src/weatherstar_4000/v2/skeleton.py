"""Generate a commented skeleton TOML config for a chosen sequence.

The skeleton enumerates every registered plugin (Screen/Component/Media/
Datasource) with its declared configurable defaults, plus a sample
``[sequences.<name>]`` section, so a user has a starting point that passes
validation for the plugins referenced by the sequence.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from weatherstar_4000.v2 import registry
from weatherstar_4000.v2.config_file import ENV_SEQUENCE

KIND_ORDER = ("datasource", "media", "component", "screen")


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


def _render_scope_lines(kind: str, name: str, defaults: dict[str, Any]) -> list[str]:
    lines = [f"[{kind}.{name}]"]
    for key, value in defaults.items():
        if value == "<required>":
            lines.append("# REQUIRED - supply a value for this key.")
            lines.append(f'# {key} = "value"')
        else:
            lines.append(f"{key} = {_toml_repr(value)}")
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
        "# Generated per-plugin from declared ConfigValue defaults.",
        "",
        f"# Sequence to execute (override with --sequence or {ENV_SEQUENCE}).",
        f'sequence = "{sequence_name}"',
        "",
    ]

    # Screen-specific generated skeleton: start from every registered screen.
    screens: list[str] = []
    if screen_names is None:
        screens = registry.registry.names("screen")
    else:
        screens = list(screen_names)

    parts.append(f"[sequences.{sequence_name}]")
    parts.append("# Global default seconds per slide (per-slide `pause` overrides).")
    parts.append("pause = 15.0")
    parts.append("slides = [")
    for name in screens:
        parts.append(f'    {{ screen = "{name}" }},')
    parts.append("]")
    parts.append("")

    for kind in include_kinds:
        for name in registry.registry.names(kind):
            cls = registry.registry.get(kind, name)
            parts.extend(_render_scope_lines(kind, name, cls.default_config()))

    parts.append("[logging]")
    parts.append('level = "INFO"')
    parts.append("console = true")
    parts.append('# file = "logs/weatherstar.jsonl"  # enables JSON structured file sink')
    parts.append("")

    return "\n".join(parts)

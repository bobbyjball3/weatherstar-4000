"""TOML configuration loading for the WeatherStar 4000 v2 engine.

Discovery order for the config file:
    1. ``--config`` CLI value
    2. ``WEATHERSTAR_CONFIG`` environment variable
    3. ``~/.config/weatherstar4000/config.toml`` (XDG default)

The engine requires either a discoverable config file or explicit CLI arguments
covering the sequence/location, per the refactor requirements.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 backport
    import tomli as tomllib

from weatherstar_4000.v2.errors import ConfigError, SequenceError

ENV_CONFIG = "WEATHERSTAR_CONFIG"
ENV_SEQUENCE = "WEATHERSTAR_SEQUENCE"
DEFAULT_FILE = Path.home() / ".config" / "weatherstar4000" / "config.toml"


def xdg_config_file() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "weatherstar4000" / "config.toml"


def discover_config_path(explicit: str | None = None) -> Path | None:
    """Return the config path to use, or None if none can be found."""
    if explicit:
        return Path(explicit)
    env = os.environ.get(ENV_CONFIG)
    if env:
        return Path(env)
    default = xdg_config_file()
    if default.exists():
        return default
    return None


def load_toml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    try:
        with open(path, "rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc


class AppConfig:
    """Typed-ish view over the raw parsed configuration dict."""

    def __init__(self, data: dict[str, Any], *, path: Path | None = None):
        self.data = data
        self.path = path

    # -- sections ----------------------------------------------------------

    def scope(self, kind: str, name: str) -> dict[str, Any]:
        """Return the config scope dict for a plugin, or {} when absent."""
        return dict(self.data.get(kind, {}).get(name, {}) or {})

    def scopes(self, kind: str) -> dict[str, dict[str, Any]]:
        return {name: dict(scope) for name, scope in (self.data.get(kind) or {}).items()}

    # -- sequence selection -------------------------------------------------

    def default_sequence(self) -> str | None:
        value = self.data.get("sequence")
        return str(value) if value else None

    def sequence_names(self) -> list[str]:
        return sorted((self.data.get("sequences") or {}).keys())

    def get_sequence(self, name: str) -> dict[str, Any]:
        sequences = self.data.get("sequences") or {}
        if name not in sequences:
            raise SequenceError(
                f"Sequence {name!r} is not defined in the config. "
                f"Available sequences: {', '.join(sorted(sequences)) or '(none)'}."
            )
        return dict(sequences[name])

    def select_sequence(self, cli_value: str | None = None) -> tuple[str, dict[str, Any]]:
        """Resolve the sequence name from CLI > envvar > config ``sequence`` key."""
        name = cli_value or os.environ.get(ENV_SEQUENCE) or self.default_sequence()
        if not name:
            raise ConfigError(
                "No sequence specified. Pass --sequence, set "
                f"{ENV_SEQUENCE}, or add a top-level `sequence` key to the config."
            )
        return name, self.get_sequence(name)

    # -- logging options -----------------------------------------------------

    def logging_options(self) -> dict[str, Any]:
        raw = self.data.get("logging") or {}
        return {
            "level": raw.get("level", "INFO"),
            "console": raw.get("console", True),
            "log_file": raw.get("file"),
        }

    # -- video options ---------------------------------------------------------

    def video_options(self) -> dict[str, Any]:
        raw = self.data.get("video") or {}
        return {
            "width": int(raw.get("width", 640)),
            "height": int(raw.get("height", 480)),
            "fps": int(raw.get("fps", 30)),
        }

    # -- location options ------------------------------------------------------

    def location_options(self) -> dict[str, Any]:
        raw = self.data.get("location") or {}
        return {
            "lat": raw.get("lat"),
            "lon": raw.get("lon"),
            "auto_detect": bool(raw.get("auto_detect", True)),
            "description": raw.get("description"),
        }

    # -- module-level conveniences ------------------------------------------

    @classmethod
    def from_file(cls, path: Path) -> AppConfig:
        return cls(load_toml(path), path=path)

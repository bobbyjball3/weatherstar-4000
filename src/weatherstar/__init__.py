"""Weather Star: a plugin-driven local forecast simulator.

The application is built around the Screen / Component / Media / Datasource /
Sequence plugin abstractions: concrete plugins self-register via the ``@plugin``
decorator and are wired into sequences from TOML configuration.
"""

import os

# Hide pygame's noisy "Hello from the pygame community" import banner.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from weatherstar.errors import (  # noqa: E402
    ConfigError,
    InvalidConfiguration,
    PluginNotFound,
    SequenceError,
    WeatherStarError,
)
from weatherstar.plugin import Plugin  # noqa: E402

__all__ = [
    "ConfigError",
    "InvalidConfiguration",
    "Plugin",
    "PluginNotFound",
    "SequenceError",
    "WeatherStarError",
]

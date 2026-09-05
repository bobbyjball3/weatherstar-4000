"""WeatherStar 4000 v2: plugin-driven refactor of the render engine.

The existing ``weatherstar_4000`` application is preserved in place; this
package is a parallel, configurable implementation built around the
Screen / Component / Media / Datasource / Sequence abstractions.
"""

import os

# Hide pygame's noisy "Hello from the pygame community" import banner.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from weatherstar_4000.v2.config import MISSING, ConfigValue, Sensitive  # noqa: E402
from weatherstar_4000.v2.errors import (  # noqa: E402
    ConfigError,
    InvalidConfiguration,
    PluginNotFound,
    SequenceError,
    WeatherStarError,
)
from weatherstar_4000.v2.plugin import Plugin  # noqa: E402

__all__ = [
    "MISSING",
    "ConfigError",
    "ConfigValue",
    "InvalidConfiguration",
    "Plugin",
    "PluginNotFound",
    "Sensitive",
    "SequenceError",
    "WeatherStarError",
]

"""Local news datasource: city label + headline sourcing for the news screens.

Self-contained replacement for the legacy Google-News-backed client.  Headlines
come from a bundled simulated pool so the screen always has content (offline
friendly).  City naming defers to the weather datasource (via the screen), so
this datasource only supplies headlines; a real feed can be added later behind
the same two methods.
"""

from __future__ import annotations

from typing import ClassVar

from weatherstar_4000.datasources.base import Datasource
from weatherstar_4000.registry import plugin

#: (title, url) pairs of simulated local headlines.
_SIMULATED_HEADLINES: list[tuple[str, str]] = [
    ("Afternoon storms likely; clearing by evening", "https://example.com/weather/storms"),
    ("City council approves new downtown transit plan", "https://example.com/news/transit"),
    ("Local food bank launches weekend drive", "https://example.com/news/foodbank"),
    ("County parks add miles of new trails", "https://example.com/news/parks"),
    ("School board sets fall calendar", "https://example.com/news/schools"),
    ("Coastal cleanup draws record volunteers", "https://example.com/news/cleanup"),
    ("Farmers market returns to the square Saturday", "https://example.com/news/market"),
    ("Library announces expanded summer hours", "https://example.com/news/library"),
    ("Utility crews to inspect power lines this week", "https://example.com/news/utility"),
    ("Community theater opens season with local classic", "https://example.com/news/theater"),
    ("Highway resurfacing begins Monday night", "https://example.com/news/highway"),
    ("Animal shelter waives adoption fees this weekend", "https://example.com/news/shelter"),
]


@plugin
class LocalNewsDatasource(Datasource):
    name = "local_news"

    _default_cache_ttl: ClassVar[int] = 3600

    def city_name(self, lat: float, lon: float) -> str:
        """Return a city label; empty lets the screen fall back to weather data."""
        return ""

    def headlines(self, lat: float, lon: float) -> list[tuple[str, str]]:
        """Return a list of ``(title, url)`` local headlines."""
        key = self._cache_key("headlines", round(lat, 2), round(lon, 2))
        cached = self.cache_get(key, 3600)
        if cached is not None:
            return cached
        self.cache_set(key, list(_SIMULATED_HEADLINES))
        return list(_SIMULATED_HEADLINES)

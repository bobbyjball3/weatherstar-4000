"""Local news datasource: city-name + headline sourcing for the news screens.

Tries real Google News + NOAA alert headlines first and falls back to the
bundled simulated headlines.  City names resolve via the NOAA weather datasource
(no separate network call) when available.
"""

from __future__ import annotations

from weatherstar_4000.v2.datasource import Datasource
from weatherstar_4000.v2.registry import plugin

try:
    from weatherstar_4000 import get_local_news_real as _real_news
except Exception:  # pragma: no cover - defensive import
    _real_news = None

from weatherstar_4000 import get_local_news as _simulated_news


@plugin
class LocalNewsDatasource(Datasource):
    name = "local_news"

    def __init__(self, cache_ttl: int = 900):
        super().__init__(cache_ttl=cache_ttl)

    def city_name(self, lat: float, lon: float) -> str:
        key = self._cache_key("city", lat, lon)
        cached = self.cache_get(key, 3600)
        if cached is not None:
            return cached
        name = ""
        if _real_news is not None:
            try:
                name = _real_news.get_city_name_from_coords(lat, lon)
            except Exception:  # noqa: BLE001
                name = ""
        if not name:
            try:
                name = _simulated_news.get_city_name_from_coords(lat, lon)
            except Exception:  # noqa: BLE001
                name = ""
        self.cache_set(key, name)
        return name

    def headlines(self, lat: float, lon: float) -> list[tuple[str, str]]:
        key = self._cache_key("headlines", lat, lon)
        cached = self.cache_get(key)
        if cached is not None:
            return cached
        items: list[tuple[str, str]] = []
        if _real_news is not None:
            try:
                items = _real_news.get_local_news_by_location(lat, lon) or []
            except Exception:  # noqa: BLE001
                items = []
        if not items:
            try:
                items = _simulated_news.get_local_news_by_location(lat, lon) or []
            except Exception:  # noqa: BLE001
                items = []
        items = items[:12]
        self.cache_set(key, items)
        return items

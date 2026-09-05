"""History datasource: 30-day temperature/precipitation history.

Adapts the (pure, decoupled) ``weatherstar_4000.history_graphs`` client behind
the Datasource plugin interface.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import PrivateAttr

from weatherstar_4000.history_graphs import get_weather_history
from weatherstar_4000.v2.datasource import Datasource
from weatherstar_4000.v2.registry import plugin


@plugin
class HistoryDatasource(Datasource):
    name = "history"

    _default_cache_ttl: ClassVar[int] = 3600

    _client: Any = PrivateAttr(default_factory=get_weather_history)

    def refresh(self, lat: float, lon: float) -> bool:
        return bool(self._client.fetch_history_data(lat, lon))

    def temperature(self, lat: float, lon: float) -> list[tuple]:
        self.refresh(lat, lon)
        return self._client.history_data.get("temperature", [])

    def precipitation(self, lat: float, lon: float) -> list[tuple]:
        self.refresh(lat, lon)
        return self._client.history_data.get("precipitation", [])

    def scroll(self, current_time: float) -> None:
        self._client.update_scroll(current_time)

    @property
    def scroll_offsets(self) -> tuple[float, float]:
        return self._client.scroll_offset_temp, self._client.scroll_offset_precip

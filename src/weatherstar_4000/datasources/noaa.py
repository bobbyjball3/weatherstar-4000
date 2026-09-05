"""NOAA weather datasource.

Replicates the data contract of the legacy NOAA client (grid point -> stations
-> observations/forecast/hourly) so ported screens receive the same shapes.
All HTTP goes through the base Datasource helpers with TTL caching.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import PrivateAttr

from weatherstar_4000.datasources.base import Datasource
from weatherstar_4000.registry import plugin

BASE_URL = "https://api.weather.gov"


@plugin
class NoaaWeather(Datasource):
    name = "weather"

    _default_cache_ttl: ClassVar[int] = 300

    _grid_cache: dict[str, dict[str, Any]] = PrivateAttr(default_factory=dict)

    # -- grid point ----------------------------------------------------------

    def _cache_key_for(self, *parts: Any) -> str:
        return super()._cache_key("noaa", *parts)

    def get_point(self, lat: float, lon: float) -> dict | None:
        key = self._cache_key_for("point", lat, lon)
        cached = self.cache_get(key, 3600)
        if cached is not None:
            return cached
        url = f"{BASE_URL}/points/{lat:.4f},{lon:.4f}"
        data = self.http_get_json(url)
        if data and "properties" in data:
            props = data["properties"]
            self.cache_set(key, props)
            return props
        return None

    def _observation_stations(self, lat: float, lon: float) -> list[str]:
        point = self.get_point(lat, lon)
        if not point:
            return []
        stations_url = point.get("observationStations")
        if not stations_url:
            return []
        key = self._cache_key_for("stations", stations_url)
        cached = self.cache_get(key, 3600)
        if cached is not None:
            return cached
        data = self.http_get_json(stations_url)
        stations: list[str] = []
        if data and "features" in data:
            for feature in data["features"]:
                station_id = feature.get("properties", {}).get("stationIdentifier")
                if station_id:
                    stations.append(station_id)
            # Prefer 4-letter identifiers that don't start with U/C.
            preferred = [s for s in stations if len(s) == 4 and s[0] not in "UC"]
            if preferred:
                stations = preferred + [s for s in stations if s not in preferred]
        self.cache_set(key, stations)
        return stations

    def _station(self, lat: float, lon: float) -> str | None:
        stations = self._observation_stations(lat, lon)
        return stations[0] if stations else None

    # -- typed fetches ---------------------------------------------------------

    def get_current(self, lat: float, lon: float) -> dict | None:
        station = self._station(lat, lon)
        if not station:
            return None
        key = self._cache_key_for("current", station)
        cached = self.cache_get(key, 300)
        if cached is not None:
            return cached
        url = f"{BASE_URL}/stations/{station}/observations/latest"
        data = self.http_get_json(url)
        if data and "properties" in data:
            props = data["properties"]
            self.cache_set(key, props)
            return props
        return None

    def _grid(self, lat: float, lon: float) -> tuple[str, int, int] | None:
        point = self.get_point(lat, lon)
        if not point:
            return None
        office = point.get("gridId")
        grid_x = point.get("gridX")
        grid_y = point.get("gridY")
        if not office or grid_x is None or grid_y is None:
            return None
        return office, int(grid_x), int(grid_y)

    def get_forecast(self, lat: float, lon: float, units: str = "us") -> dict | None:
        grid = self._grid(lat, lon)
        if not grid:
            return None
        office, grid_x, grid_y = grid
        key = self._cache_key_for("forecast", office, grid_x, grid_y, units)
        cached = self.cache_get(key, 1800)
        if cached is not None:
            return cached
        url = f"{BASE_URL}/gridpoints/{office}/{grid_x},{grid_y}/forecast"
        data = self.http_get_json(url, params={"units": units})
        if data and "properties" in data:
            props = data["properties"]
            self.cache_set(key, props)
            return props
        return None

    def get_hourly(self, lat: float, lon: float, units: str = "us") -> dict | None:
        grid = self._grid(lat, lon)
        if not grid:
            return None
        office, grid_x, grid_y = grid
        key = self._cache_key_for("hourly", office, grid_x, grid_y, units)
        cached = self.cache_get(key, 1800)
        if cached is not None:
            return cached
        url = f"{BASE_URL}/gridpoints/{office}/{grid_x},{grid_y}/forecast/hourly"
        data = self.http_get_json(url, params={"units": units})
        if data and "properties" in data:
            props = data["properties"]
            self.cache_set(key, props)
            return props
        return None

    # -- location info ---------------------------------------------------------

    def get_city(self, lat: float, lon: float) -> tuple[str, str]:
        """Return (city, state) resolved from the NOAA grid point, or ("", "")."""
        point = self.get_point(lat, lon)
        if not point:
            return "", ""
        rel = point.get("relativeLocation", {}).get("properties", {})
        return rel.get("city", ""), rel.get("state", "")

    def get_radar_station(self, lat: float, lon: float) -> str | None:
        point = self.get_point(lat, lon)
        if point:
            return point.get("radarStation")
        return None

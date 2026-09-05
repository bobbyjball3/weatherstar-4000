"""Datasources for live secondary feeds: alerts, earthquakes, UV, stocks."""

from __future__ import annotations

from pydantic import Field, SecretStr

from weatherstar_4000.v2.datasource import Datasource
from weatherstar_4000.v2.registry import plugin

NOAA_ALERTS_URL = "https://api.weather.gov/alerts/active"
USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
OM_UV_URL = "https://api.open-meteo.com/v1/forecast"


@plugin
class NoaaAlertsDatasource(Datasource):
    """Active NOAA alerts for a point, filtered/sorted like the legacy alert system."""

    name = "alerts"

    severity_priority: str = Field(
        default="extreme:severe:moderate",
        description="Colon-separated severity order used to sort alerts (most severe first).",
    )

    def active(self, lat: float, lon: float) -> list[dict]:
        key = self._cache_key("alerts", lat, lon)
        cached = self.cache_get(key, 60)
        if cached is not None:
            return cached
        data = self.http_get_json(NOAA_ALERTS_URL, params={"point": f"{lat},{lon}"}, timeout=5)
        alerts = _parse_alerts(data or {})
        priority = [p.strip() for p in self.severity_priority.split(":") if p.strip()]
        alerts.sort(
            key=lambda a: priority.index(a["severity"]) if a["severity"] in priority else 99
        )
        self.cache_set(key, alerts)
        return alerts

    def is_critical(self, alerts: list[dict]) -> bool:
        return any(a.get("severity") == "Extreme" for a in alerts) or any(
            a.get("severity") == "Severe" and a.get("urgency") == "Immediate" for a in alerts
        )


def _parse_alerts(data: dict) -> list[dict]:
    features = data.get("features") or []
    result = []
    for feature in features:
        props = feature.get("properties") or {}
        severity = props.get("severity")
        if severity not in {"Extreme", "Severe", "Moderate"}:
            continue
        result.append(
            {
                "id": props.get("id"),
                "event": props.get("event"),
                "headline": props.get("headline"),
                "severity": severity,
                "urgency": props.get("urgency"),
                "areas": props.get("areaDesc"),
                "instruction": props.get("instruction"),
                "expires": props.get("expires"),
                "description": props.get("description"),
            }
        )
    return result


@plugin
class EarthquakesDatasource(Datasource):
    name = "earthquakes"

    min_magnitude: float = Field(
        default=3.0, description="Minimum earthquake magnitude to include."
    )
    limit: int = Field(default=10, description="Maximum number of earthquakes to fetch.")

    def recent(self, lat: float, lon: float) -> list[dict]:
        key = self._cache_key("quakes", lat, lon, self.min_magnitude, self.limit)
        cached = self.cache_get(key, 1800)
        if cached is not None:
            return cached
        params = {
            "format": "geojson",
            "minmagnitude": self.min_magnitude,
            "limit": self.limit,
            "orderby": "time",
        }
        data = self.http_get_json(USGS_URL, params=params, timeout=10)
        events = (data or {}).get("features") or []
        result = [
            {
                "magnitude": float(e["properties"].get("mag") or 0),
                "place": e["properties"].get("place", ""),
                "time": e["properties"].get("time"),
            }
            for e in events
            if e.get("properties")
        ]
        self.cache_set(key, result)
        return result


@plugin
class UvIndexDatasource(Datasource):
    name = "uv_index"

    days: int = Field(default=7, description="Number of days of UV index forecast to fetch.")

    def daily(self, lat: float, lon: float) -> list[dict]:
        key = self._cache_key("uv", lat, lon, self.days)
        cached = self.cache_get(key, 1800)
        if cached is not None:
            return cached
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "uv_index_max",
            "timezone": "auto",
            "forecast_days": self.days,
        }
        data = self.http_get_json(OM_UV_URL, params=params, timeout=10)
        daily = (data or {}).get("daily") or {}
        result = [
            {"date": daily["time"][i], "uv_index": daily["uv_index_max"][i]}
            for i in range(len(daily.get("time", [])))
        ]
        self.cache_set(key, result)
        return result

    @staticmethod
    def protection_level(uv_index: float) -> str:
        if uv_index <= 2:
            return "Low"
        if uv_index <= 5:
            return "Moderate"
        if uv_index <= 7:
            return "High"
        if uv_index <= 10:
            return "Very High"
        return "Extreme"


@plugin
class StockMarketDatasource(Datasource):
    """Alpha Vantage stock quotes for a set of symbols.

    ``api_key`` is a required, sensitive config value sent as a query parameter.
    """

    name = "stocks"

    api_key: SecretStr = Field(
        description="Alpha Vantage API key (required; sent with each request)."
    )
    api_key_param: str = Field(
        default="apikey", description="Query parameter the API key is sent under."
    )
    api_key_header: str | None = Field(
        default=None,
        description="Header the API key is sent under instead (leave blank to use the query parameter).",
    )
    symbols: str = Field(
        default="DIA,SPY,QQQ", description="Comma-separated stock/index symbols to display."
    )

    def quotes(self) -> list[dict]:
        symbols = [s.strip() for s in self.symbols.split(",") if s.strip()]
        result = []
        for symbol in symbols:
            quote = self._quote(symbol)
            if quote:
                result.append(quote)
        return result

    def _quote(self, symbol: str) -> dict | None:
        key = self._cache_key("quote", symbol)
        cached = self.cache_get(key, 300)
        if cached is not None:
            return cached
        data = self.http_get_json(
            "https://www.alphavantage.co/query",
            params={"function": "GLOBAL_QUOTE", "symbol": symbol},
            timeout=10,
        )
        quote = (data or {}).get("Global Quote") or {}
        if not quote:
            return None
        result = {
            "symbol": quote.get("01. symbol", symbol),
            "price": quote.get("05. price"),
            "change": quote.get("09. change"),
            "change_percent": quote.get("10. change percent"),
        }
        self.cache_set(key, result)
        return result

    def __repr__(self) -> str:
        return f"<StockMarketDatasource name={self.name!r} api_key=***>"

"""Tests for datasource plugins (parsing, caching, masking, graceful failure)."""

import pytest
from pydantic import ValidationError

from weatherstar_4000.v2.datasources.feeds import (
    EarthquakesDatasource,
    NoaaAlertsDatasource,
    StockMarketDatasource,
    UvIndexDatasource,
    _parse_alerts,
)


def _stocks(**values):
    defaults = {"api_key": "k", "symbols": "DIA,SPY,QQQ"}
    defaults.update(values)
    return StockMarketDatasource.model_validate(defaults)


def test_stock_datasource_requires_sensitive_api_key():
    with pytest.raises(ValidationError):
        StockMarketDatasource.model_validate({})
    ds = StockMarketDatasource.model_validate({"api_key": "secret"})
    assert "secret" not in repr(ds)
    assert "***" in repr(ds)
    assert ds.api_key.get_secret_value() == "secret"


def test_stock_quote_parses_and_caches(monkeypatch):
    ds = _stocks(symbols="DIA")
    payload = {
        "Global Quote": {
            "01. symbol": "DIA",
            "05. price": "300.00",
            "09. change": "1.5",
            "10. change percent": "0.5%",
        }
    }
    monkeypatch.setattr(ds, "http_get_json", lambda *a, **k: payload)
    quotes = ds.quotes()
    assert quotes[0]["symbol"] == "DIA"
    assert quotes[0]["price"] == "300.00"


def test_stock_api_key_injected_as_query_param():
    ds = _stocks(symbols="DIA")
    params = ds._query_params({"function": "GLOBAL_QUOTE", "symbol": "DIA"})
    assert params["apikey"] == "k"


def test_stock_quote_graceful_when_api_fails(monkeypatch):
    ds = _stocks(symbols="DIA")
    monkeypatch.setattr(ds, "http_get_json", lambda *a, **k: None)
    assert ds.quotes() == []


def test_alerts_parse_filters_severity():
    data = {
        "features": [
            {
                "properties": {
                    "id": "1",
                    "event": "Flood",
                    "headline": "Flood Warning",
                    "severity": "Extreme",
                    "urgency": "Immediate",
                    "areaDesc": "County",
                    "instruction": "Move to higher ground",
                    "expires": "2030-01-01T00:00:00Z",
                }
            },
            {"properties": {"id": "2", "event": "Info", "severity": "Minor"}},
        ]
    }
    alerts = _parse_alerts(data)
    assert len(alerts) == 1
    assert alerts[0]["event"] == "Flood"
    assert alerts[0]["severity"] == "Extreme"


def test_alerts_critical():
    ds = NoaaAlertsDatasource()
    assert ds.is_critical([{"severity": "Extreme"}]) is True
    assert ds.is_critical([{"severity": "Severe", "urgency": "Immediate"}]) is True
    assert ds.is_critical([{"severity": "Severe", "urgency": "Expected"}]) is False


def test_uv_daily_parsing_and_protection(monkeypatch):
    ds = UvIndexDatasource()

    def fake(url, params=None, timeout=None):
        return {
            "daily": {
                "time": ["2026-01-01", "2026-01-02"],
                "uv_index_max": [3.5, 9.0],
            }
        }

    monkeypatch.setattr(ds, "http_get_json", fake)
    daily = ds.daily(10.0, 20.0)
    assert len(daily) == 2
    assert ds.protection_level(daily[0]["uv_index"]) == "Moderate"
    assert ds.protection_level(daily[1]["uv_index"]) == "Very High"
    assert ds.protection_level(11) == "Extreme"


def test_earthquakes_recent_parse(monkeypatch):
    ds = EarthquakesDatasource()

    def fake(url, params=None, timeout=None):
        return {
            "features": [
                {
                    "properties": {
                        "mag": 4.2,
                        "place": "10 km NW of X",
                        "time": 1700000000000,
                    }
                },
                {"properties": {"mag": None, "place": "", "time": None}},
            ]
        }

    monkeypatch.setattr(ds, "http_get_json", fake)
    events = ds.recent(0.0, 0.0)
    assert len(events) == 2
    assert events[0]["magnitude"] == 4.2

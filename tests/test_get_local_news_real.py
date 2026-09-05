"""Tests for the real (Google News RSS) local news fetcher."""

from unittest.mock import patch

import pytest

from weatherstar_4000 import get_local_news_real

RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss><channel>{items}</channel></rss>
"""

ITEM_TEMPLATE = "<item><title>{title}</title><link>{link}</link><pubDate>Wed, 01 Jan 2026 00:00:00 GMT</pubDate></item>"


# --- clean_html ------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, cleaned",
    [
        ("<b>Hello</b>", "Hello"),
        ("<a href='x'>link text</a>", "link text"),
        ("no tags here", "no tags here"),
        ("<p>One</p><p>Two</p>", "OneTwo"),
    ],
)
def test_clean_html_removes_tags(raw, cleaned):
    # Assert
    assert get_local_news_real.clean_html(raw) == cleaned


# --- fetch_google_news -----------------------------------------------------


def test_fetch_google_news_parses_rss_and_prefixes_local():
    # Arrange
    titles = [
        "City Council Meets - CNN",
        "Sports Update",
        "Breaking: Storm Coming - BBC",
        "Market Report",
        "Weather Tomorrow",
        "Traffic Jam",
    ]
    items = "".join(
        ITEM_TEMPLATE.format(title=t, link=f"https://news/{i}") for i, t in enumerate(titles)
    )

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = RSS_TEMPLATE.format(items=items).encode()

        # Act
        headlines = get_local_news_real.fetch_google_news("Springfield")

    # Assert
    # Enough headlines so no additional topic searches happen.
    assert len(headlines) == 6
    texts = [h for h, _ in headlines]
    assert "Local: City Council Meets" in texts  # source suffix stripped + prefixed
    assert "Local: Sports Update" in texts
    assert "Breaking: Storm Coming" in texts  # Breaking kept as-is, no double prefix
    assert "Local: Market Report" in texts


def test_fetch_google_news_returns_empty_on_error():
    with patch("requests.get", side_effect=Exception("down")):
        # Act
        result = get_local_news_real.fetch_google_news("Springfield")

        # Assert
        assert result == []


def test_fetch_google_news_runs_topic_searches_when_sparse():
    # Arrange
    main_titles = ["Only One Story Here - AP"]
    topic_titles = ["Traffic Update", "City Events"]
    responses = [None, None, None]

    def fake_get(*args, **kwargs):
        idx = [i for i, r in enumerate(responses) if r is None][0]
        responses[idx] = True
        titles = main_titles if idx == 0 else [topic_titles[idx - 1]]

        class _Resp:
            status_code = 200
            content = RSS_TEMPLATE.format(
                items="".join(ITEM_TEMPLATE.format(title=t, link="https://news/x") for t in titles)
            ).encode()

        return _Resp()

    with patch("requests.get", side_effect=fake_get):
        # Act
        headlines = get_local_news_real.fetch_google_news("Springfield")

    # Assert
    # Three requests: one main feed + two topic searches.
    assert len(headlines) == 3


# --- fetch_weather_alerts --------------------------------------------------


def test_fetch_weather_alerts_parses_severe_and_moderate():
    # Arrange
    features = [
        {
            "properties": {
                "id": "abc123",
                "event": "Tornado Warning",
                "severity": "Severe",
            }
        },
        {
            "properties": {
                "id": "def456",
                "event": "Flood Watch",
                "severity": "Moderate",
            }
        },
    ]

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"features": features}

        # Act
        alerts = get_local_news_real.fetch_weather_alerts(40.0, -74.0)

    # Assert
    assert alerts[0] == (
        "Alert: Tornado Warning in Effect",
        "https://www.weather.gov/alerts/abc123",
    )
    assert alerts[1][0] == "Weather: Flood Watch Issued"


def test_fetch_weather_alerts_returns_empty_when_no_features():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"features": []}

        # Act
        result = get_local_news_real.fetch_weather_alerts(40.0, -74.0)

        # Assert
        assert result == []


def test_fetch_weather_alerts_returns_empty_on_error():
    with patch("requests.get", side_effect=Exception("down")):
        # Act
        result = get_local_news_real.fetch_weather_alerts(40.0, -74.0)

        # Assert
        assert result == []


# --- get_fallback_headlines ------------------------------------------------


def test_get_fallback_headlines_include_city():
    # Act
    headlines = get_local_news_real.get_fallback_headlines("Springfield")

    # Assert
    assert any("Springfield" in headline for headline, _ in headlines)
    assert len(headlines) == 10


# --- get_city_name_from_coords ---------------------------------------------


def test_get_city_name_returns_city_and_state():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"address": {"city": "New York", "state": "NY"}}

        # Act
        result = get_local_news_real.get_city_name_from_coords(40.7, -74.0)

        # Assert
        assert result == "New York, NY"


def test_get_city_name_defaults_on_exception():
    with patch("requests.get", side_effect=Exception("down")):
        # Act
        result = get_local_news_real.get_city_name_from_coords(0.0, 0.0)

        # Assert
        assert result == "Local Area"


# --- get_local_news_by_location ---------------------------------------------


def test_get_local_news_by_location_uses_google_headlines(monkeypatch):
    # Arrange
    google = [
        ("Local: A", "u1"),
        ("Local: B", "u2"),
        ("Local: C", "u3"),
        ("Local: D", "u4"),
        ("Local: E", "u5"),
    ]
    monkeypatch.setattr(get_local_news_real, "get_city_name_from_coords", lambda *a: "Springfield")
    monkeypatch.setattr(get_local_news_real, "fetch_google_news", lambda *a: google)
    weather = [("Alert: Storm", "u6")]
    monkeypatch.setattr(get_local_news_real, "fetch_weather_alerts", lambda *a: weather)
    fallback = [("Fallback", "u")]
    monkeypatch.setattr(get_local_news_real, "get_fallback_headlines", lambda *a: fallback)

    # Act
    result = get_local_news_real.get_local_news_by_location(40.0, -74.0)

    # Assert
    assert result == google


def test_get_local_news_by_location_extends_with_weather(monkeypatch):
    # Arrange
    google = [("Local: A", "u1"), ("Local: B", "u2")]
    weather = [("Alert: Storm", "u3"), ("Weather: Rain", "u4"), ("Alert: Flood", "u5")]
    expected = list(google) + weather  # snapshot before fetch mutates the shared list
    monkeypatch.setattr(get_local_news_real, "get_city_name_from_coords", lambda *a: "Springfield")
    monkeypatch.setattr(get_local_news_real, "fetch_google_news", lambda *a: google)
    monkeypatch.setattr(get_local_news_real, "fetch_weather_alerts", lambda *a: weather)
    fallback = [("Fallback", "u")]
    monkeypatch.setattr(get_local_news_real, "get_fallback_headlines", lambda *a: fallback)

    # Act
    result = get_local_news_real.get_local_news_by_location(40.0, -74.0)

    # Assert
    assert result == expected


def test_get_local_news_by_location_falls_back_when_sparse(monkeypatch):
    # Arrange
    google = [("Local: A", "u1")]
    weather = [("Alert: Storm", "u2")]
    fallback = [("Local: Springfield Community News", "https://news.google.com")]
    monkeypatch.setattr(get_local_news_real, "get_city_name_from_coords", lambda *a: "Springfield")
    monkeypatch.setattr(get_local_news_real, "fetch_google_news", lambda *a: google)
    monkeypatch.setattr(get_local_news_real, "fetch_weather_alerts", lambda *a: weather)
    monkeypatch.setattr(get_local_news_real, "get_fallback_headlines", lambda *a: fallback)

    # Act
    result = get_local_news_real.get_local_news_by_location(40.0, -74.0)

    # Assert
    assert result == fallback


def test_get_local_news_by_location_falls_back_on_error(monkeypatch):
    # Arrange
    monkeypatch.setattr(
        get_local_news_real,
        "get_city_name_from_coords",
        lambda *a: (_ for _ in ()).throw(ValueError),
    )
    fallback = [("Local: Local Area Community News", "u")]
    monkeypatch.setattr(get_local_news_real, "get_fallback_headlines", lambda *a: fallback)

    # Act
    result = get_local_news_real.get_local_news_by_location(40.0, -74.0)

    # Assert
    assert result == fallback


def test_get_local_news_by_location_truncates_to_twelve(monkeypatch):
    # Arrange
    many = [(f"Local: Story {i}", f"u{i}") for i in range(15)]
    monkeypatch.setattr(get_local_news_real, "get_city_name_from_coords", lambda *a: "Springfield")
    monkeypatch.setattr(get_local_news_real, "fetch_google_news", lambda *a: many)

    # Act
    result = get_local_news_real.get_local_news_by_location(40.0, -74.0)

    # Assert
    assert len(result) == 12

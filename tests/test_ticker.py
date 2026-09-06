"""Tests for the bottom scrolling ticker."""

import time

import pygame

from weatherstar_4000.context import AppContext, DataRegistry, Location
from weatherstar_4000.ticker import (
    SCROLL_SPEED,
    BottomTicker,
    WeatherStar3000Scroll,
)


def _ctx(surface, description="Orlando"):
    fonts = {"scroller": pygame.font.Font(None, 24), "normal": pygame.font.Font(None, 20)}
    return AppContext(
        surface=surface,
        fonts=fonts,
        assets={},
        data=DataRegistry(),
        location=Location(lat=28.54, lon=-81.38, description=description),
    )


def test_ticker_builds_current_conditions_items(screen):
    from weatherstar_4000.datasources.noaa import (
        City,
        CurrentConditions,
        ForecastPeriod,
    )

    class _Weather:
        def get_city(self, lat, lon):
            return City(city="Orlando", state="FL")

        def get_current(self, lat, lon):
            return CurrentConditions(
                temperature_c=27.0,
                text_description="Partly Cloudy",
                relative_humidity=60.0,
                wind_speed_kmh=4.0,
                wind_direction=180.0,
            )

        def get_forecast(self, lat, lon):
            return [
                ForecastPeriod(name="Today", temperature=90.0, short_forecast="Sunny"),
                ForecastPeriod(name="Tonight", temperature=72.0, short_forecast="Clear"),
            ]

    ctx = _ctx(screen)
    ctx.data.register("weather", _Weather())
    ticker = BottomTicker()
    items = ticker._build_items(ctx)
    text = " ".join(items)
    assert "ORLANDO, FL" in text
    assert "81" in text  # 27C -> ~81F
    assert "60%" in text
    assert "TODAY: 90" in text


def test_ticker_falls_back_without_weather(screen):
    ctx = _ctx(screen)
    ticker = BottomTicker()
    assert ticker._build_items(ctx)


def test_ticker_scrolls_left_by_speed_times_dt(screen):
    ctx = _ctx(screen)
    ticker = BottomTicker()
    ticker._items = ["A" * 30]
    ticker._current = ticker._items[0]
    ticker._x = 500.0
    ticker._last_refresh = time.time()
    ticker.render(screen, ctx, 1.0)
    assert ticker._x == 500.0 - SCROLL_SPEED


def test_ticker_cycles_to_next_item_when_offscreen(screen):
    ctx = _ctx(screen)
    ticker = BottomTicker()
    ticker._items = ["X", "YYYYYYYYYYYYYYYYYYYYYY"]
    ticker._current = "X"
    ticker._x = 5.0  # one character width; a 1s step at 100px/s clears it
    ticker._last_refresh = time.time()
    ticker.render(screen, ctx, 1.0)
    assert ticker._current == "YYYYYYYYYYYYYYYYYYYYYY"
    assert ticker._x > 600.0  # wrapped back to the right edge


def test_ticker_draws_text_in_banner_band(screen):
    ctx = _ctx(screen)
    ticker = BottomTicker()
    ticker._items = ["HELLO TICKER"]
    ticker._current = ticker._items[0]
    ticker._x = 200.0
    ticker._last_refresh = time.time()
    ticker.render(screen, ctx, 0.0)
    white_pixels = 0
    for x in range(0, 640, 2):
        for y in range(428, 462):
            if screen.get_at((x, y))[:3] == (255, 255, 255):
                white_pixels += 1
    assert white_pixels > 0


def test_ws3000_scroll_draws_date_time_and_conditions(screen):
    ctx = _ctx(screen)
    ctx.fonts["large"] = pygame.font.Font(None, 28)
    band = WeatherStar3000Scroll()
    band._items = ["HELLO 3000 SCROLL"]
    band.render(screen, ctx, 0.1)
    white_pixels = sum(
        1
        for x in range(0, 640, 2)
        for y in range(400, 475)
        if screen.get_at((x, y))[:3] == (255, 255, 255)
    )
    assert white_pixels > 0


def test_ws3000_scroll_rotates_short_messages(screen):
    ctx = _ctx(screen)
    ctx.fonts["large"] = pygame.font.Font(None, 28)
    band = WeatherStar3000Scroll()
    band._items = ["SHORT A", "SHORT B"]
    # 10s of frames: each short message holds ~8s before rotating.
    for _ in range(200):
        band.render(screen, ctx, 0.05)
    assert band._message_index == 1


def test_ws3000_scroll_uppercases_conditions(screen):
    ctx = _ctx(screen)
    band = WeatherStar3000Scroll()
    items = band._conditions(ctx)
    assert items and items[0] == items[0].upper()

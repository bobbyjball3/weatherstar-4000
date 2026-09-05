"""Tests for the shared Renderer helper mixin (font/color/data/layout helpers)."""

import pygame

from weatherstar_4000.context import AppContext, DataRegistry, Location
from weatherstar_4000.renderer import Renderer
from weatherstar_4000.themes import CLASSIC_THEME


class _Dummy(Renderer):
    """Concrete subclass under test (stand-in for Screen/Component)."""


def _ctx(surface, *, fonts=None, assets=None, data=None, location=None):
    return AppContext(
        surface=surface,
        theme=CLASSIC_THEME,
        fonts=fonts or {},
        assets=assets or {},
        data=data or DataRegistry(),
        location=location,
    )


def test_font_returns_named_font(screen):
    fonts = {"small": pygame.font.Font(None, 10), "normal": pygame.font.Font(None, 20)}
    ctx = _ctx(screen, fonts=fonts)
    assert _Dummy().font(ctx, "small") is fonts["small"]


def test_font_falls_back_to_first_loaded(screen):
    fonts = {"small": pygame.font.Font(None, 10)}
    ctx = _ctx(screen, fonts=fonts)
    assert _Dummy().font(ctx, "missing") is fonts["small"]


def test_font_creates_default_when_no_fonts(screen):
    assert _Dummy().font(_ctx(screen), "normal").size("x")[0] > 0


def test_color_uses_theme(screen):
    ctx = _ctx(screen)
    assert _Dummy().color(ctx, "yellow") == ctx.colors["yellow"]


def test_color_fallback(screen):
    ctx = _ctx(screen)
    assert _Dummy().color(ctx, "nope", (1, 2, 3)) == (1, 2, 3)
    assert _Dummy().color(ctx, "nope") == (255, 255, 255)


def test_text_surface_and_blit_text(screen):
    renderer = _Dummy()
    ctx = _ctx(screen, fonts={"normal": pygame.font.Font(None, 20)})
    surf = renderer.text_surface(ctx, "hello", color_key="yellow")
    assert surf.get_width() > 0
    rect = renderer.blit_text(screen, ctx, "hello", (10, 10), color_key="yellow")
    assert rect.topleft == (10, 10)


def test_datasource_lookup(screen):
    ds = object()
    data = DataRegistry()
    data.register("weather", ds)
    ctx = _ctx(screen, data=data)
    assert _Dummy().datasource(ctx, "weather") is ds
    assert _Dummy().datasource(ctx, "missing") is None
    assert _Dummy().datasource(_ctx(screen), "weather") is None


def test_latlon(screen):
    ctx = _ctx(screen, location=Location(lat=28.5, lon=-81.3))
    assert _Dummy().latlon(ctx) == (28.5, -81.3)
    assert _Dummy().latlon(_ctx(screen)) == (0.0, 0.0)


def test_wrap_honors_max_width(screen):
    font = pygame.font.Font(None, 20)
    renderer = _Dummy()
    lines = renderer.wrap(font, "one two three four five", 80)
    assert lines
    for line in lines:
        assert font.size(line)[0] <= 80
    assert " ".join(lines) == "one two three four five"


def test_centered_draws_and_returns_rect(screen):
    ctx = _ctx(screen, fonts={"small": pygame.font.Font(None, 20)})
    rect = _Dummy().centered(screen, ctx, "hi", 100, font_name="small")
    assert rect.centery == 100
    assert rect.centerx == screen.get_width() // 2


def test_fahrenheit_conversions(screen):
    renderer = _Dummy()
    assert renderer.fahrenheit(0) == 32
    assert renderer.fahrenheit(100) == 212
    assert renderer.fahrenheit(None) is None
    assert renderer.fahrenheit("bad") is None


def test_cardinal_points(screen):
    renderer = _Dummy()
    assert renderer.cardinal(0) == "N"
    assert renderer.cardinal(90) == "E"
    assert renderer.cardinal(360) == "N"
    assert renderer.cardinal(None) == ""
    assert renderer.cardinal("bad") == ""


def test_format_date(screen):
    renderer = _Dummy()
    assert renderer.format_date("2026-01-05") == "Mon 01/05"
    assert renderer.format_date("") == ""
    assert renderer.format_date("not-a-date") == "not-a-date"


def test_num_and_measure(screen):
    renderer = _Dummy()
    props = {"temperature": {"value": 30.5}, "missing": None}
    assert renderer.num(props, "temperature") == 30.5
    assert renderer.num(props, "missing") is None
    assert renderer.measure(props, "pressure", "barometricPressure") is None
    assert renderer.measure({"pressure": 101500}, "pressure", "barometricPressure") == 101500.0
    assert renderer.measure({"pressure": {"value": 12}}, "pressure") == 12.0
    assert renderer.measure({"pressure": "bad"}, "pressure") is None
    assert renderer.num(None, "temperature") is None


def test_text_field(screen):
    renderer = _Dummy()
    assert renderer.text({"textDescription": "Partly Cloudy"}, "textDescription") == "Partly Cloudy"
    assert renderer.text({"parts": ["a", "b"]}, "parts") == "a b"
    assert renderer.text({"textDescription": "Partly Cloudy"}, "textDescription", 6) == "Partly"
    assert renderer.text(None, "anything") == ""
    assert renderer.text({"n": 7}, "n") == "7"


def test_weather_data(screen):
    class _Weather:
        def get_current(self, lat, lon):
            return {"lat": lat, "lon": lon}

        def get_city(self, lat, lon):
            return ("Melbourne", "FL")

    data = DataRegistry()
    data.register("weather", _Weather())
    ctx = _ctx(screen, data=data, location=Location(lat=28.5, lon=-81.3))
    renderer = _Dummy()
    result = renderer.weather_data(ctx, "get_current")
    assert result == {"lat": 28.5, "lon": -81.3}
    assert renderer.weather_data(_ctx(screen), "get_current") is None
    assert renderer.weather_data(ctx, "missing_method") is None


def test_icon_helpers(screen):
    renderer = _Dummy()
    assert renderer.icon_name("https://api.weather.gov/icons/land/day/sct?size=medium") == (
        "Partly-Cloudy"
    )
    assert renderer.icon_name("") is None

    icon = pygame.Surface((10, 10))
    icon.fill((50, 60, 70))
    ctx = _ctx(screen, assets={"icons": {"Rain": icon}})
    resolved = renderer.icon_surface(ctx, "Rain", 20, 20)
    assert resolved is not None
    assert resolved.get_size() == (20, 20)
    assert renderer.icon_surface(ctx, "Missing") is None
    assert renderer.icon_surface(ctx, None) is None

"""Weekend Forecast screen: Saturday and Sunday columns."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

_FONT_SIZES = {
    "title": 32,
    "large": 32,
    "extended": 32,
    "small": 28,
    "normal": 20,
    "forecast": 24,
    "tiny": 16,
    "scroller": 24,
}


def _ensure_fonts(ctx: Any) -> None:
    fonts = getattr(ctx, "fonts", None)
    if not isinstance(fonts, dict):
        return
    for name, size in _FONT_SIZES.items():
        fonts.setdefault(name, pygame.font.Font(None, size))


def _font(ctx: Any, name: str) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None)
    if isinstance(fonts, dict):
        found = fonts.get(name)
        if found is not None:
            return found
    return pygame.font.Font(None, _FONT_SIZES.get(name, 20))


def _color(
    ctx: Any, key: str, fallback: tuple[int, int, int] = (255, 255, 255)
) -> tuple[int, int, int]:
    try:
        return (ctx.colors or {}).get(key, fallback)
    except Exception:
        return fallback


def _weather(ctx: Any) -> Any:
    try:
        return ctx.data.get("weather")
    except Exception:
        return None


def _data(ctx: Any, method: str) -> Any:
    ds = _weather(ctx)
    if ds is None:
        return None
    fn = getattr(ds, method, None)
    loc = getattr(ctx, "location", None)
    if fn is None or loc is None:
        return None
    try:
        return fn(loc.lat, loc.lon)
    except Exception:
        return None


def _icon_name(icon_url: str) -> str | None:
    if not icon_url:
        return None
    parts = icon_url.split("/")
    if len(parts) >= 2:
        condition = parts[-1].split("?")[0]
        icon_map = {
            "skc": "Clear",
            "few": "Clear",
            "sct": "Partly-Cloudy",
            "bkn": "Cloudy",
            "ovc": "Cloudy",
            "rain": "Rain",
            "rain_showers": "Shower",
            "tsra": "Thunderstorm",
            "snow": "Light-Snow",
            "fog": "Fog",
            "wind": "Windy",
        }
        return icon_map.get(condition, "Clear")
    return None


def _icon_surface(ctx: Any, name: str | None) -> Any:
    if not name:
        return None
    try:
        mgr = getattr(ctx, "icon_manager", None)
        if mgr is None:
            mgr = (ctx.assets or {}).get("icon_manager")
        if mgr is not None:
            icon = mgr.get_icon(name)
            if icon is not None:
                return icon
    except Exception:
        pass
    try:
        icons = (ctx.assets or {}).get("icons") or {}
        return icons.get(name)
    except Exception:
        return None


def _wrap_tiny_lines(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in (text or "").split():
        test_line = f"{current} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


@plugin
class WeekendForecastScreen(Screen):
    name = "weekend_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    def _draw_day_column(
        self, surface: pygame.Surface, ctx: Any, col_x: int, title: str, periods: list[Any]
    ) -> None:
        yellow = _color(ctx, "yellow")
        cyan = _color(ctx, "cyan")
        white = _color(ctx, "white")
        col_width = 260

        y_pos = 145
        title_surf = _font(ctx, "extended").render(title, True, yellow)
        surface.blit(title_surf, title_surf.get_rect(center=(col_x + col_width // 2, y_pos)))
        y_pos += 35

        for period in periods[:2]:
            name = str(period.get("name", ""))
            time_of_day = "DAY" if "Day" in name or "Night" not in name else "NIGHT"
            tod_surf = _font(ctx, "normal").render(time_of_day, True, cyan)
            surface.blit(tod_surf, (col_x + 10, y_pos))
            y_pos += 25

            temp = period.get("temperature")
            if temp is not None:
                temp_surf = _font(ctx, "normal").render(f"{temp}\N{DEGREE SIGN}", True, white)
                surface.blit(temp_surf, (col_x + 10, y_pos))
            y_pos += 25

            icon = _icon_surface(ctx, _icon_name(str(period.get("icon", ""))))
            if icon is not None:
                orig_size = icon.get_size()
                if orig_size[0] > 0 and orig_size[1] > 0:
                    scale_factor = min(60 / orig_size[0], 60 / orig_size[1])
                    new_size = (int(orig_size[0] * scale_factor), int(orig_size[1] * scale_factor))
                    scaled = pygame.transform.scale(icon, new_size)
                    icon_x = col_x + 70 + (60 - new_size[0]) // 2
                    icon_y = y_pos - 50 + (60 - new_size[1]) // 2
                    surface.blit(scaled, (icon_x, icon_y))

            short = str(period.get("shortForecast", ""))
            lines = _wrap_tiny_lines(_font(ctx, "tiny"), short, col_width - 20)
            for line in lines[:3]:
                line_surf = _font(ctx, "tiny").render(line, True, white)
                surface.blit(line_surf, (col_x + 10, y_pos))
                y_pos += 18

            y_pos += 15

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        _ensure_fonts(ctx)
        render.draw_background(surface, ctx, "4")
        render.draw_header(surface, ctx, "Weekend", "Forecast")

        forecast = _data(ctx, "get_forecast") or {}
        try:
            periods = forecast.get("periods") or []
        except Exception:
            periods = []

        left_col_x = 60
        right_col_x = 340
        saturday_periods: list[Any] = []
        sunday_periods: list[Any] = []

        for period in periods:
            name = str(period.get("name", ""))
            if "Saturday" in name:
                saturday_periods.append(period)
            elif "Sunday" in name:
                sunday_periods.append(period)
            if len(saturday_periods) >= 2 and len(sunday_periods) >= 2:
                break

        if saturday_periods:
            self._draw_day_column(surface, ctx, left_col_x, "SATURDAY", saturday_periods)
        if sunday_periods:
            self._draw_day_column(surface, ctx, right_col_x, "SUNDAY", sunday_periods)

        if not saturday_periods and not sunday_periods:
            msg = _font(ctx, "normal").render(
                "Weekend forecast not available", True, _color(ctx, "white")
            )
            surface.blit(msg, msg.get_rect(center=(320, 240)))

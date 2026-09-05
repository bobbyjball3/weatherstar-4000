"""Extended Forecast screen: three day/night columns with hi/lo temps."""

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


def _wrap_lines(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    for word in (text or "").split():
        test_line = " ".join(current + [word])
        if font.size(test_line)[0] > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


@plugin
class ExtendedForecastScreen(Screen):
    name = "extended_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        _ensure_fonts(ctx)
        render.draw_background(surface, ctx, "3")
        render.draw_header(surface, ctx, "Extended", "Forecast")

        forecast = _data(ctx, "get_forecast") or {}
        try:
            periods = forecast.get("periods") or []
        except Exception:
            periods = []

        day_width = 155
        total_width = 640
        num_days = min(3, len(periods) // 2)

        if num_days == 0:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        total_column_width = day_width * num_days
        remaining_space = total_width - total_column_width
        side_margin = remaining_space // (num_days + 1)
        start_x = side_margin

        yellow = _color(ctx, "yellow")
        white = _color(ctx, "white")
        blue = _color(ctx, "blue")
        day_count = 0

        for i in range(0, min(len(periods), 6), 2):
            if day_count >= 3:
                break
            day_period = periods[i]
            night_period = periods[i + 1] if i + 1 < len(periods) else None

            x_pos = start_x + (day_count * (day_width + side_margin))
            col_center = x_pos + day_width // 2

            name = str(day_period.get("name", ""))
            if "Tonight" in name or "Overnight" in name:
                day_name = "TONIGHT"
            elif "Today" in name:
                day_name = "TODAY"
            else:
                day_name = name.upper().split()[0][:3] if name.split() else ""

            if day_name:
                name_surf = _font(ctx, "extended").render(day_name, True, yellow)
                surface.blit(name_surf, name_surf.get_rect(center=(col_center, 120)))

            original_icon = _icon_surface(ctx, _icon_name(str(day_period.get("icon", ""))))
            if original_icon is not None:
                orig_w, orig_h = original_icon.get_size()
                if orig_h > 0:
                    scale = 75 / orig_h
                    new_w = int(orig_w * scale)
                    new_h = 75
                    if new_w > 100 and orig_w > 0:
                        scale = 100 / orig_w
                        new_w = 100
                        new_h = int(orig_h * scale)
                else:
                    new_w, new_h = 86, 75
                icon = pygame.transform.scale(original_icon, (new_w, new_h))
                surface.blit(icon, icon.get_rect(center=(col_center, 180)))

            short_forecast = str(day_period.get("shortForecast", ""))
            lines = _wrap_lines(_font(ctx, "small"), short_forecast, day_width - 10)

            cond_y = 240
            for line in lines[:2]:
                cond_surf = _font(ctx, "small").render(line, True, white)
                surface.blit(cond_surf, cond_surf.get_rect(center=(col_center, cond_y)))
                cond_y += 25

            if day_period.get("isDaytime"):
                hi_temp = day_period.get("temperature")
                lo_temp = night_period.get("temperature") if night_period else None
            else:
                lo_temp = day_period.get("temperature")
                hi_temp = (
                    night_period.get("temperature")
                    if night_period and night_period.get("isDaytime")
                    else None
                )

            temp_block_width = int(day_width * 0.44)
            lo_x_center = x_pos + temp_block_width // 2 + 10
            if lo_temp is not None:
                lo_label = _font(ctx, "small").render("Lo", True, blue)
                surface.blit(lo_label, lo_label.get_rect(center=(lo_x_center, 310)))
                lo_surf = _font(ctx, "normal").render(f"{lo_temp}\N{DEGREE SIGN}", True, white)
                surface.blit(lo_surf, lo_surf.get_rect(center=(lo_x_center, 335)))

            hi_x_center = x_pos + day_width - temp_block_width // 2 - 10
            if hi_temp is not None:
                hi_label = _font(ctx, "small").render("Hi", True, yellow)
                surface.blit(hi_label, hi_label.get_rect(center=(hi_x_center, 310)))
                hi_surf = _font(ctx, "normal").render(f"{hi_temp}\N{DEGREE SIGN}", True, white)
                surface.blit(hi_surf, hi_surf.get_rect(center=(hi_x_center, 335)))

            day_count += 1

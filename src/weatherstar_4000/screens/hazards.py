"""Weather Hazards screen: keyword scan of the forecast, with safety tips."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

#: Keywords that flag a forecast period as hazardous (legacy scan set).
_HAZARD_WORDS = ("storm", "severe", "warning", "watch", "advisory")

#: Fallback tips shown when no hazard is detected.
_SAFETY_TIPS = (
    "\u2022 Monitor weather conditions regularly",
    "\u2022 Have an emergency kit prepared",
    "\u2022 Know your evacuation routes",
    "\u2022 Sign up for weather alerts",
)


def _font(ctx: Any, name: str, size: int) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None) or {}
    return fonts.get(name) or pygame.font.Font(None, size)


def _color(ctx: Any, key: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
    colors = getattr(ctx, "colors", None) or {}
    return colors.get(key, default)


def _ds(ctx: Any, name: str) -> Any:
    data = getattr(ctx, "data", None)
    if data is None:
        return None
    try:
        return data.get(name)
    except Exception:  # noqa: BLE001 - optional datasource
        return None


def _latlon(ctx: Any) -> tuple[float, float]:
    location = getattr(ctx, "location", None)
    if location is None:
        return 0.0, 0.0
    return float(getattr(location, "lat", 0.0)), float(getattr(location, "lon", 0.0))


@plugin
class HazardsScreen(Screen):
    name = "hazards"
    media = ("backgrounds", "fonts", "logos")
    datasources = ("weather",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "3")
        render.draw_header(surface, ctx, "Weather", "Alerts")

        white = _color(ctx, "white", (255, 255, 255))
        yellow = _color(ctx, "yellow", (255, 255, 0))
        normal = _font(ctx, "normal", 20)
        extended = _font(ctx, "extended", 24)

        y_pos = 175
        title = extended.render("CURRENT HAZARDS", True, yellow)
        surface.blit(title, (60, y_pos))
        y_pos += 40

        periods = self._forecast_periods(ctx)
        has_alerts = False

        for period in periods[:3]:
            forecast_text = str(period.get("detailedForecast", "")).lower()
            if not any(word in forecast_text for word in _HAZARD_WORDS):
                continue
            has_alerts = True
            name = period.get("name", "")
            name_text = normal.render(f"{name}:", True, yellow)
            surface.blit(name_text, (80, y_pos))
            y_pos += 25

            words = str(period.get("shortForecast", "")).split()
            line: list[str] = []
            for word in words:
                line.append(word)
                if normal.size(" ".join(line))[0] <= 480:
                    continue
                line.pop()
                if line:
                    text_surf = normal.render(" ".join(line), True, white)
                    surface.blit(text_surf, (100, y_pos))
                    y_pos += 25
                line = [word]
            if line:
                text_surf = normal.render(" ".join(line), True, white)
                surface.blit(text_surf, (100, y_pos))
                y_pos += 35

        if not has_alerts:
            no_alert = normal.render("No active weather alerts at this time", True, white)
            surface.blit(no_alert, no_alert.get_rect(center=(320, 200)))

            y_pos = 250
            tips_title = extended.render("WEATHER SAFETY TIPS", True, yellow)
            surface.blit(tips_title, (60, y_pos))
            y_pos += 35
            for tip in _SAFETY_TIPS:
                surface.blit(normal.render(tip, True, white), (80, y_pos))
                y_pos += 25

    def _forecast_periods(self, ctx: Any) -> list[dict]:
        lat, lon = _latlon(ctx)
        weather = _ds(ctx, "weather")
        if weather is None:
            return []
        try:
            forecast = weather.get_forecast(lat, lon) or {}
        except Exception:  # noqa: BLE001 - data is optional
            return []
        return list(forecast.get("periods") or [])

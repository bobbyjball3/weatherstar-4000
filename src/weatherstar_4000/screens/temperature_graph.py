"""7-Day Temperature Graph screen (port of legacy ``draw_temperature_graph``).

Builds a day/night high-low bar chart from NOAA forecast periods with
temperature-scaled gradient bars and per-day high/low labels.
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

_WHITE = (255, 255, 255)
_YELLOW = (255, 255, 0)

_GRAPH_LEFT = 80
_GRAPH_TOP = 105
_GRAPH_WIDTH = 480
_GRAPH_HEIGHT = 250
_BAR_WIDTH = 40
_GRADIENT_STEPS = 5


@plugin
class TemperatureGraphScreen(Screen):
    name = "temperature_graph"
    media = ("backgrounds",)
    datasources = ("weather",)

    @staticmethod
    def _bar_color(avg_temp: float) -> tuple[int, int, int]:
        """Pick the base bar color from the average temperature."""
        if avg_temp < 32:
            return (100, 150, 255)
        if avg_temp < 50:
            return (150, 200, 255)
        if avg_temp < 65:
            return (150, 255, 150)
        if avg_temp < 75:
            return (255, 255, 100)
        if avg_temp < 85:
            return (255, 200, 100)
        return (255, 100, 100)

    layout = (
        ComponentSpec(component="background", config={"background_name": "1-chart"}),
        ComponentSpec(
            component="header",
            config={"title_top": "7-Day", "title_bottom": "Temperature", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        colors = ctx.colors
        yellow = colors.get("yellow", _YELLOW)
        white = colors.get("white", _WHITE)

        temps, labels = self._collect_periods(ctx)
        if not temps:
            render.draw_centered_text(surface, ctx, "Forecast data unavailable", 240)
            return

        min_temp = min(t for pair in temps for t in pair) - 5
        max_temp = max(t for pair in temps for t in pair) + 5
        temp_range = max_temp - min_temp

        pygame.draw.line(
            surface,
            white,
            (_GRAPH_LEFT, _GRAPH_TOP + _GRAPH_HEIGHT),
            (_GRAPH_LEFT + _GRAPH_WIDTH, _GRAPH_TOP + _GRAPH_HEIGHT),
            2,
        )
        pygame.draw.line(
            surface,
            white,
            (_GRAPH_LEFT, _GRAPH_TOP),
            (_GRAPH_LEFT, _GRAPH_TOP + _GRAPH_HEIGHT),
            2,
        )

        font_small = self.font(ctx, "small")
        bar_width = _GRAPH_WIDTH // len(temps)
        for i, ((high, low), label) in enumerate(zip(temps, labels)):
            x = _GRAPH_LEFT + i * bar_width + bar_width // 2

            high_y = _GRAPH_TOP + _GRAPH_HEIGHT - ((high - min_temp) / temp_range * _GRAPH_HEIGHT)
            low_y = _GRAPH_TOP + _GRAPH_HEIGHT - ((low - min_temp) / temp_range * _GRAPH_HEIGHT)

            bar_x = x - 20
            bar_height = abs(low_y - high_y)
            bar_color = self._bar_color((high + low) / 2)

            step_height = bar_height / _GRADIENT_STEPS
            for j in range(_GRADIENT_STEPS):
                factor = j / _GRADIENT_STEPS
                step_color = (
                    min(255, int(bar_color[0] * (1 - factor * 0.3))),
                    min(255, int(bar_color[1] * (1 - factor * 0.3))),
                    min(255, int(bar_color[2] * (1 - factor * 0.3))),
                )
                pygame.draw.rect(
                    surface,
                    step_color,
                    (bar_x, high_y + j * step_height, _BAR_WIDTH, step_height + 1),
                )

            if font_small is not None:
                high_text = font_small.render(str(high), True, yellow)
                surface.blit(high_text, high_text.get_rect(center=(x, high_y - 10)))
                low_text = font_small.render(str(low), True, white)
                surface.blit(low_text, low_text.get_rect(center=(x, low_y + 20)))
                label_text = font_small.render(label, True, white)
                label_rect = label_text.get_rect(center=(x, _GRAPH_TOP + _GRAPH_HEIGHT + 10))
                surface.blit(label_text, label_rect)

    def _collect_periods(self, ctx: Any) -> tuple[list[tuple[int, int]], list[str]]:
        """Return (high, low) pairs + day labels from up to 7 forecast days."""
        try:
            weather = ctx.data.get("weather")
            location = ctx.location
            if weather is None or location is None:
                return [], []
            forecast = weather.get_forecast(location.lat, location.lon)
            periods = (forecast or {}).get("periods") or []
        except Exception:
            return [], []

        temps: list[tuple[int, int]] = []
        labels: list[str] = []
        for i in range(0, min(len(periods), 14), 2):
            if i >= len(periods):
                break
            day_period = periods[i]
            night_period = periods[i + 1] if i + 1 < len(periods) else None

            if day_period.get("isDaytime"):
                high = day_period.get("temperature")
                low = night_period.get("temperature") if night_period else None
                if high is None:
                    continue
                if low is None:
                    low = high - 10
            else:
                low = day_period.get("temperature")
                high = night_period.get("temperature") if night_period else None
                if low is None:
                    continue
                if high is None:
                    high = low + 10

            try:
                temps.append((int(high), int(low)))
            except (TypeError, ValueError):
                continue
            labels.append((day_period.get("name") or "")[:3].upper())

        return temps, labels

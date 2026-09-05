"""Wind & Pressure screen (port of legacy ``draw_wind_pressure``).

Reads the NOAA current-conditions properties (wind, gust, wind chill/heat
index, pressure) and shows a simulated steady trend arrow.
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
_SOFT_RED = (255, 100, 100)

# m/s -> mph
_MS_TO_MPH = 2.23694
# Pa -> inches of mercury
_PA_TO_INHG = 0.00029530


@plugin
class WindPressureScreen(Screen):
    name = "wind_pressure"
    media = ("backgrounds",)
    datasources = ("weather",)

    layout = (
        ComponentSpec(component="background", config={"background_name": "1"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Wind &", "title_bottom": "Pressure", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        colors = ctx.colors
        yellow = colors.get("yellow", _YELLOW)
        white = colors.get("white", _WHITE)

        current = self._current_conditions(ctx)
        if not current:
            render.draw_centered_text(surface, ctx, "Current conditions unavailable", 240)
            return

        y_pos = 120
        self.blit_text(
            surface, ctx, "WIND CONDITIONS", (60, y_pos), font_name="extended", color=yellow
        )
        y_pos += 35

        wind_speed = self.measure(current, "windSpeed")
        wind_dir = self.measure(current, "windDirection")
        wind_gust = self.measure(current, "windGust")

        if wind_speed is not None:
            wind_mph = int(wind_speed * _MS_TO_MPH)
            self.blit_text(
                surface, ctx, f"Speed: {wind_mph} mph", (80, y_pos), font_name="normal", color=white
            )
            y_pos += 30

        if wind_dir is not None:
            dir_text = self.cardinal(wind_dir)
            self.blit_text(
                surface,
                ctx,
                f"Direction: {dir_text} ({wind_dir:.0f}\u00b0)",
                (80, y_pos),
                font_name="normal",
                color=white,
            )
            y_pos += 30

        if wind_gust is not None:
            gust_mph = int(wind_gust * _MS_TO_MPH)
            self.blit_text(
                surface,
                ctx,
                f"Gusts: {gust_mph} mph",
                (80, y_pos),
                font_name="normal",
                color=yellow,
            )
            y_pos += 30

        wind_chill = self.measure(current, "windChill")
        heat_index = self.measure(current, "heatIndex")
        if wind_chill is not None:
            wc_f = int(wind_chill * 9 / 5 + 32)
            blue = colors.get("blue", (128, 128, 255))
            self.blit_text(
                surface,
                ctx,
                f"Wind Chill: {wc_f}\u00b0F",
                (80, y_pos),
                font_name="normal",
                color=blue,
            )
            y_pos += 30
        elif heat_index is not None:
            hi_f = int(heat_index * 9 / 5 + 32)
            self.blit_text(
                surface,
                ctx,
                f"Heat Index: {hi_f}\u00b0F",
                (80, y_pos),
                font_name="normal",
                color=_SOFT_RED,
            )
            y_pos += 30

        y_pos += 20
        self.blit_text(
            surface, ctx, "BAROMETRIC PRESSURE", (60, y_pos), font_name="extended", color=yellow
        )
        y_pos += 35

        pressure = self.measure(current, "pressure", "barometricPressure")
        if pressure is not None:
            pressure_inhg = pressure * _PA_TO_INHG
            self.blit_text(
                surface,
                ctx,
                f"Current: {pressure_inhg:.2f} in",
                (80, y_pos),
                font_name="normal",
                color=white,
            )
            y_pos += 30

            font_normal = self.font(ctx, "normal")
            if font_normal is not None:
                trend = font_normal.render("Trend: Steady", True, white)
                surface.blit(trend, (80, y_pos))
                arrow_x = 80 + trend.get_width() + 14
                pygame.draw.polygon(
                    surface,
                    white,
                    [(arrow_x + 10, y_pos + 12), (arrow_x, y_pos + 4), (arrow_x, y_pos + 20)],
                )

    @staticmethod
    def _current_conditions(ctx: Any) -> dict:
        try:
            weather = ctx.data.get("weather")
            location = ctx.location
            if weather is None or location is None:
                return {}
            current = weather.get_current(location.lat, location.lon)
        except Exception:
            return {}
        return current or {}

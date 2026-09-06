"""Wind & Pressure screen (port of legacy ``draw_wind_pressure``).

Reads the typed current-conditions model (wind, gust, wind chill/heat index,
pressure) and shows a simulated steady trend arrow.
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.datasources.noaa import CurrentConditions
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen

_WHITE = (255, 255, 255)
_YELLOW = (255, 255, 0)
_SOFT_RED = (255, 100, 100)


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

        current: CurrentConditions | None = self.weather_data(ctx, "get_current")
        if current is None:
            render.draw_centered_text(surface, ctx, "Current conditions unavailable", 240)
            return

        y_pos = 120
        self.blit_text(
            surface, ctx, "WIND CONDITIONS", (60, y_pos), font_name="extended", color=yellow
        )
        y_pos += 35

        wind_mph = current.wind_mph
        if wind_mph is not None:
            self.blit_text(
                surface, ctx, f"Speed: {wind_mph} mph", (80, y_pos), font_name="normal", color=white
            )
            y_pos += 30

        wind_dir = current.wind_direction
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

        wind_gust_mph = current.wind_gust_mph
        if wind_gust_mph is not None:
            self.blit_text(
                surface,
                ctx,
                f"Gusts: {wind_gust_mph} mph",
                (80, y_pos),
                font_name="normal",
                color=yellow,
            )
            y_pos += 30

        wind_chill_f = current.wind_chill_f
        heat_index_f = current.heat_index_f
        if wind_chill_f is not None:
            blue = colors.get("blue", (128, 128, 255))
            self.blit_text(
                surface,
                ctx,
                f"Wind Chill: {wind_chill_f}\u00b0F",
                (80, y_pos),
                font_name="normal",
                color=blue,
            )
            y_pos += 30
        elif heat_index_f is not None:
            self.blit_text(
                surface,
                ctx,
                f"Heat Index: {heat_index_f}\u00b0F",
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

        pressure_inhg = current.pressure_inhg
        if pressure_inhg is not None:
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
            trend = font_normal.render("Trend: Steady", True, white)
            surface.blit(trend, (80, y_pos))
            arrow_x = 80 + trend.get_width() + 14
            pygame.draw.polygon(
                surface,
                white,
                [(arrow_x + 10, y_pos + 12), (arrow_x, y_pos + 4), (arrow_x, y_pos + 20)],
            )

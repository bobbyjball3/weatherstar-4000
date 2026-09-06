"""Regional Forecast screen: today's outlook for cities across the region.

The WeatherStar 3000 calls this "Forecast Across The Region": a City / Weather /
Low / Hi table (ws3kp _regional-forecast.scss) fed by each nearby station's own
gridpoint forecast, so nearby places can show different conditions.  The screen
has no classic WeatherStar 4000 equivalent, so the classic look is the same
table in the standard fonts.
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.datasources.noaa import RegionalForecast
from weatherstar_4000.registry import plugin
from weatherstar_4000.renderer import short_condition_text
from weatherstar_4000.screens.base import Screen
from weatherstar_4000.themes import LayoutVariant

#: Table geometry shared by both looks (ws3kp columns: weather x280, low right
#: 70, high right 0 relative to the content box whose left sits at ``_LEFT``).
_LEFT = 40
_RIGHT = 600
_COL_WEATHER_X = 320
_COL_WEATHER_END = 505
_COL_LOW_RIGHT = 530
_COL_HIGH_RIGHT = 600
_HEADER_Y = 104
_ROW_TOP = 132
_ROW_HEIGHT = 38


@plugin
class RegionalForecastScreen(Screen):
    name = "regional_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    variants = {
        LayoutVariant.WS4000: "compose_4000",
        LayoutVariant.WS3000: "compose_3000",
    }

    layout = (
        ComponentSpec(component="background", config={"background_name": "5"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Regional", "title_bottom": "Forecast", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        self._compose_table(surface, ctx, "normal")

    def compose_3000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        self._compose_table(surface, ctx, "extended")

    def _compose_table(self, surface: pygame.Surface, ctx: Any, row_font_name: str) -> None:
        rows: list[RegionalForecast] = self.weather_data(ctx, "get_regional_forecast") or []
        if not rows:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 250, font_name="large", color_key="yellow"
            )
            return

        header_color = self.color(ctx, "yellow")
        self._draw_table(surface, ctx, rows, row_font_name, header_color)

    # -- shared table --------------------------------------------------------

    def _draw_table(
        self,
        surface: pygame.Surface,
        ctx: Any,
        rows: list[RegionalForecast],
        row_font_name: str,
        header_color,
    ) -> None:
        white = self.color(ctx, "white")
        header_font = self.font(ctx, "small")
        headers = ("CITY", "WEATHER", "LOW", "HI")
        positions = (
            (_LEFT, "left"),
            (_COL_WEATHER_X, "left"),
            (_COL_LOW_RIGHT, "right"),
            (_COL_HIGH_RIGHT, "right"),
        )
        for text, (x, align) in zip(headers, positions):
            rect = header_font.render(text, True, header_color).get_rect()
            rect.topleft = (x, _HEADER_Y)
            if align == "right":
                rect.right = x
            self.draw_text(surface, ctx, text, rect, font_name="small", color=header_color)

        row_font = self.font(ctx, row_font_name)
        y = _ROW_TOP
        for row in rows[:7]:
            city = row.location.upper()
            if not city:
                city = "STATION"
            if self.font(ctx, row_font_name).size(city)[0] > _COL_WEATHER_X - _LEFT:
                city = self._fit(city, row_font, _COL_WEATHER_X - _LEFT)
            self.draw_text(surface, ctx, city, (_LEFT, y), font_name=row_font_name, color=white)

            weather = short_condition_text(row.weather).upper()
            if weather:
                weather = self._fit(weather, row_font, _COL_WEATHER_END - _COL_WEATHER_X)
                self.draw_text(
                    surface, ctx, weather, (_COL_WEATHER_X, y), font_name=row_font_name, color=white
                )

            if row.low_f is not None:
                low = f"{row.low_f}\N{DEGREE SIGN}"
                surf = row_font.render(low, True, white)
                self.draw_text(
                    surface,
                    ctx,
                    low,
                    surf.get_rect(right=_COL_LOW_RIGHT, y=y),
                    font_name=row_font_name,
                    color=white,
                )
            if row.high_f is not None:
                high = f"{row.high_f}\N{DEGREE SIGN}"
                surf = row_font.render(high, True, white)
                self.draw_text(
                    surface,
                    ctx,
                    high,
                    surf.get_rect(right=_COL_HIGH_RIGHT, y=y),
                    font_name=row_font_name,
                    color=white,
                )
            y += _ROW_HEIGHT

    @staticmethod
    def _fit(text: str, font: pygame.font.Font, max_width: int) -> str:
        """Shorten ``text`` to the longest prefix fitting ``max_width`` px."""
        if font.size(text)[0] <= max_width:
            return text
        for length in range(len(text), 0, -1):
            if font.size(text[:length])[0] <= max_width:
                return text[:length]
        return text[:1]

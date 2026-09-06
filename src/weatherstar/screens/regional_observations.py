"""Regional Observations screen: nearby-station observation table.

The classic look shows a single nearest station's latest observation; the
Weather Star 3000 variant is the ws3kp "Latest Hourly Observations" table with
one row per nearby station (location / temperature / weather / wind).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar import render
from weatherstar.components.base import ComponentSpec
from weatherstar.datasources.noaa import CurrentConditions
from weatherstar.registry import plugin
from weatherstar.renderer import short_condition_text
from weatherstar.screens.base import Screen
from weatherstar.themes import LayoutVariant

#: Weather Star 3000 table geometry (ws3kp _latest-observations.scss columns).
_TABLE_LEFT = 40
_TABLE_RIGHT = 600
_COL_TEMP_X = 320
_COL_WEATHER_X = 368
_COL_WEATHER_END = 505
_HEADER_Y = 104
_ROW_TOP = 132
_ROW_HEIGHT = 38


@plugin
class RegionalObservationsScreen(Screen):
    name = "regional_observations"
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
            config={"title_top": "Latest", "title_bottom": "Observations", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        current: CurrentConditions | None = self.weather_data(ctx, "get_current")
        if current is None:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        white = self.color(ctx, "white")
        yellow = self.color(ctx, "yellow")
        y_pos = 120

        station = current.station or "Station"
        station_surf = self.font(ctx, "normal").render(f"Station: {station}", True, yellow)
        surface.blit(station_surf, (60, y_pos))
        y_pos += 40

        temp_f = current.temperature_f
        if temp_f is not None:
            temp_surf = self.font(ctx, "normal").render(
                f"Temperature: {temp_f}\N{DEGREE SIGN}", True, white
            )
            surface.blit(temp_surf, (60, y_pos))
            y_pos += 30

        wind_mph = current.wind_mph
        if wind_mph is not None:
            wind_surf = self.font(ctx, "normal").render(f"Wind: {wind_mph} mph", True, white)
            surface.blit(wind_surf, (60, y_pos))
            y_pos += 30

        timestamp = current.timestamp
        if timestamp:
            try:
                obs_time = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                time_str = obs_time.strftime("%I:%M %p %m/%d").lstrip("0")
                time_surf = self.font(ctx, "normal").render(f"Observed: {time_str}", True, white)
                surface.blit(time_surf, (60, y_pos))
            except (ValueError, TypeError):
                pass

    # -- Weather Star 3000 (ws3kp) variant ------------------------------------

    def compose_3000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        """ws3kp Latest Hourly Observations: one row per nearby station.

        Column headers run in the small face (Location / °F / Weather / Wind),
        then up to seven 24pt rows of station conditions (see
        _latest-observations.scss: temp at x280, weather x330, wind x480).
        """
        white = self.color(ctx, "white")
        rows: list[CurrentConditions] = self.weather_data(ctx, "get_observations") or []
        if not rows:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 250, font_name="large", color_key="yellow"
            )
            return

        header_font = self.font(ctx, "small")
        headers = ("LOCATION", "\N{DEGREE SIGN}F", "WEATHER", "WIND")
        header_xs = (_TABLE_LEFT, _COL_TEMP_X, _COL_WEATHER_X, _TABLE_RIGHT)
        header_aligns = ("left", "left", "left", "right")
        for text, x, align in zip(headers, header_xs, header_aligns):
            rect = header_font.render(text, True, white).get_rect()
            rect.topleft = (x, _HEADER_Y)
            if align == "right":
                rect.right = _TABLE_RIGHT
            self.draw_text(surface, ctx, text, rect, font_name="small", color=white)

        row_font = self.font(ctx, "extended")
        y = _ROW_TOP
        for observation in rows[:7]:
            location = (observation.station_name or observation.station or "Station").upper()
            location = location[: _fit_prefix(location, row_font, _COL_TEMP_X - _TABLE_LEFT)]
            if not location:
                location = "STATION"
            self.draw_text(
                surface, ctx, location, (_TABLE_LEFT, y), font_name="extended", color=white
            )

            temp_f = observation.temperature_f
            if temp_f is not None:
                self.draw_text(
                    surface,
                    ctx,
                    f"{temp_f}\N{DEGREE SIGN}",
                    (_COL_TEMP_X, y),
                    font_name="extended",
                    color=white,
                )

            condition = short_condition_text(observation.text_description)
            condition = condition[
                : _fit_prefix(condition, row_font, _COL_WEATHER_END - _COL_WEATHER_X)
            ]
            if condition:
                self.draw_text(
                    surface, ctx, condition, (_COL_WEATHER_X, y), font_name="extended", color=white
                )

            wind = self._wind_text(observation)
            if wind:
                wind_surf = row_font.render(wind, True, white)
                self.draw_text(
                    surface,
                    ctx,
                    wind,
                    wind_surf.get_rect(right=_TABLE_RIGHT, y=y),
                    font_name="extended",
                    color=white,
                )
            y += _ROW_HEIGHT

    @staticmethod
    def _wind_text(observation: CurrentConditions) -> str:
        wind_mph = observation.wind_mph
        if wind_mph is None:
            return ""
        if wind_mph <= 0:
            return "CALM"
        degrees = observation.wind_direction
        if degrees is None:
            return f"{wind_mph}"
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        try:
            direction = directions[int((degrees + 11.25) / 22.5) % 16]
        except (TypeError, ValueError):
            direction = ""
        return f"{direction} {wind_mph}".strip().upper()


def _fit_prefix(text: str, font: pygame.font.Font, max_width: int) -> int:
    """Longest prefix of ``text`` (in chars) that fits ``max_width`` px."""
    if not text:
        return 0
    if font.size(text)[0] <= max_width:
        return len(text)
    for length in range(len(text), 0, -1):
        if font.size(text[:length])[0] <= max_width:
            return length
    return 1

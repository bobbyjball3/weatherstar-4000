"""Weather Almanac screen: statistics for the day plus sun & moon."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pygame

from weatherstar.components.base import ComponentSpec
from weatherstar.datasources.noaa import CurrentConditions
from weatherstar.ephemeris import next_moon_phases, sun_clock_minutes
from weatherstar.registry import plugin
from weatherstar.screens.base import Screen
from weatherstar.themes import LayoutVariant

#: Weather Star 3000 almanac geometry: a right-aligned three-column sun table
#: (label | today | tomorrow) over a centered moon-phases list.
_LABEL_RIGHT = 205
_TODAY_RIGHT = 385
_TOMORROW_RIGHT = 600
_ALMANAC_LEFT = 35
_SUN_TOP = 96
_SUN_GAP = 42
_MOON_HEADING_Y = 240
_MOON_TOP = 278
_MOON_GAP = 32


@plugin
class AlmanacScreen(Screen):
    name = "almanac"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    variants = {
        LayoutVariant.WS4000: "compose_4000",
        LayoutVariant.WS3000: "compose_3000",
    }

    layout = (
        ComponentSpec(component="background", config={"background_name": "4"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Weather", "title_bottom": "Almanac", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        current: CurrentConditions = self.weather_data(ctx, "get_current") or CurrentConditions()
        white = self.color(ctx, "white")
        yellow = self.color(ctx, "yellow")

        date_str = datetime.now().strftime("%B %d, %Y")
        date_surf = self.font(ctx, "normal").render(
            f"Weather Statistics for {date_str}", True, yellow
        )
        surface.blit(date_surf, date_surf.get_rect(center=(320, 100)))

        y_pos = 128
        stats_title = self.font(ctx, "extended").render("CURRENT CONDITIONS", True, yellow)
        surface.blit(stats_title, (60, y_pos))
        y_pos += 30

        temp_f = current.temperature_f
        if temp_f is not None:
            row = self.font(ctx, "normal").render(
                f"Temperature: {temp_f}\N{DEGREE SIGN}F", True, white
            )
            surface.blit(row, (80, y_pos))
            y_pos += 24

        humidity = current.relative_humidity
        if humidity is not None:
            row = self.font(ctx, "normal").render(f"Humidity: {humidity:.0f}%", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 24

        dewpoint_f = current.dewpoint_f
        if dewpoint_f is not None:
            row = self.font(ctx, "normal").render(
                f"Dewpoint: {dewpoint_f}\N{DEGREE SIGN}F", True, white
            )
            surface.blit(row, (80, y_pos))
            y_pos += 24

        pressure_inhg = current.pressure_inhg
        if pressure_inhg is not None:
            row = self.font(ctx, "normal").render(f"Pressure: {pressure_inhg:.2f} in", True, white)
            surface.blit(row, (80, y_pos))
            y_pos += 24

        visibility_miles = current.visibility_miles
        if visibility_miles is not None:
            row = self.font(ctx, "normal").render(
                f"Visibility: {visibility_miles:.1f} miles", True, white
            )
            surface.blit(row, (80, y_pos))
            y_pos += 30

        y_pos += 8
        sun_title = self.font(ctx, "extended").render("SUN & MOON", True, yellow)
        surface.blit(sun_title, (60, y_pos))
        y_pos += 30

        sunrise_surf = self.font(ctx, "normal").render("Sunrise: 6:45 AM", True, white)
        surface.blit(sunrise_surf, (80, y_pos))
        y_pos += 24

        sunset_surf = self.font(ctx, "normal").render("Sunset: 7:30 PM", True, white)
        surface.blit(sunset_surf, (80, y_pos))
        y_pos += 24

        moon_surf = self.font(ctx, "normal").render("Moon Phase: Waxing Gibbous", True, white)
        surface.blit(moon_surf, (80, y_pos))

    # -- Weather Star 3000 (ws3kp) variant ------------------------------------

    def compose_3000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        """ws3kp Almanac: sunrise/sunset for today & tomorrow, then moon phases.

        Three right-aligned columns carry (label | today | tomorrow) for the
        sun rows; the weekday names head the two value columns.  Below, a
        centered "Moon Phases" heading introduces the next four phase dates.
        """
        white = self.color(ctx, "white")
        yellow = self.color(ctx, "yellow")
        font = self.font(ctx, "extended")
        lat, lon = self.latlon(ctx)
        today = date.today()
        tomorrow = today + timedelta(days=1)

        sunrise_today, sunset_today = sun_clock_minutes(today, lat, lon)
        sunrise_tomorrow, sunset_tomorrow = sun_clock_minutes(tomorrow, lat, lon)

        def right(text: str, x_right: int, y: int, font_name: str = "extended", color=None):
            surf = self.font(ctx, font_name).render(text, True, color or white)
            self.draw_text(
                surface,
                ctx,
                text,
                surf.get_rect(right=x_right, y=y),
                font_name=font_name,
                color=color or white,
            )

        def left(text: str, x: int, y: int, font_name: str = "extended", color=None):
            self.draw_text(surface, ctx, text, (x, y), font_name=font_name, color=color or white)

        # -- sun table ------------------------------------------------------
        y = _SUN_TOP
        left("", _ALMANAC_LEFT, y)  # blank label cell
        right(today.strftime("%A").upper(), _TODAY_RIGHT, y)
        right(tomorrow.strftime("%A").upper(), _TOMORROW_RIGHT, y)
        y += _SUN_GAP

        left("SUNRISE", _ALMANAC_LEFT, y)
        right(self._format_clock(sunrise_today), _TODAY_RIGHT, y)
        right(self._format_clock(sunrise_tomorrow), _TOMORROW_RIGHT, y)
        y += _SUN_GAP

        left("SUNSET", _ALMANAC_LEFT, y)
        right(self._format_clock(sunset_today), _TODAY_RIGHT, y)
        right(self._format_clock(sunset_tomorrow), _TOMORROW_RIGHT, y)

        # -- moon phases ------------------------------------------------------
        heading = font.render("MOON PHASES", True, yellow)
        self.draw_text(
            surface,
            ctx,
            "MOON PHASES",
            heading.get_rect(center=(surface.get_width() // 2, _MOON_HEADING_Y)),
            font_name="extended",
            color=yellow,
        )

        phases = next_moon_phases(today)
        y = _MOON_TOP
        for name, when in phases:
            right(name, _LABEL_RIGHT, y)
            right(when.strftime("%b %d").upper().replace(" 0", " "), _TOMORROW_RIGHT, y)
            y += _MOON_GAP

    @staticmethod
    def _format_clock(minutes: int) -> str:
        """Minutes since midnight -> ``7:24 AM`` (12-hour, ws3kp style)."""
        minutes = int(minutes) % 1440
        hour_24 = minutes // 60
        minute = minutes % 60
        suffix = "AM" if hour_24 < 12 else "PM"
        hour_12 = hour_24 % 12 or 12
        return f"{hour_12}:{minute:02d} {suffix}"

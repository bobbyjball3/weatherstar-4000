"""Hourly Forecast screen: continuously scrolling hour-by-hour listing."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar import render
from weatherstar.components.base import ComponentSpec
from weatherstar.datasources.noaa import ForecastPeriod
from weatherstar.registry import plugin
from weatherstar.screens.base import Screen
from weatherstar.themes import LayoutVariant


@plugin
class HourlyForecastScreen(Screen):
    name = "hourly_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    variants = {
        LayoutVariant.WS4000: "compose_4000",
    }

    layout = (
        ComponentSpec(component="background", config={"background_name": "5"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Hourly", "title_bottom": "Forecast", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        periods: list[ForecastPeriod] = self.weather_data(ctx, "get_hourly") or []
        if not periods:
            periods = self.weather_data(ctx, "get_forecast") or []

        yellow = self.color(ctx, "yellow")
        white = self.color(ctx, "white")

        if not periods:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        content_top = 120
        content_height = 250
        line_height = 25
        total_lines = len(periods[:24])
        total_content_height = total_lines * line_height

        # The list fills its clip region from the top edge and rolls upward;
        # the band is kept well clear of the bottom ticker/footer (y>=410).
        scroll_time = pygame.time.get_ticks() // 50
        scroll_offset = scroll_time % total_content_height

        header_surf = self.font(ctx, "small").render("TIME  TEMP  CONDITIONS", True, yellow)
        surface.blit(header_surf, (65, content_top))

        clip_top = content_top + 30
        clip_rect = pygame.Rect(0, clip_top, 640, content_height)
        surface.set_clip(clip_rect)

        base_y = clip_top - scroll_offset
        for loop in range(2):
            y_offset = loop * total_content_height
            for i, period in enumerate(periods[:24]):
                y_pos = base_y + y_offset + (i * line_height)
                if clip_top - line_height <= y_pos <= clip_top + content_height:
                    start_time = period.start_time
                    time_display = ""
                    if start_time:
                        time_display = start_time.strftime("%I %p").lstrip("0").rjust(7)
                    if not time_display:
                        time_display = period.name[:7].rjust(7)

                    temp = period.temperature
                    if temp is None:
                        temp = 0
                    temp_display = f"{int(temp):3}\N{DEGREE SIGN}"

                    short = period.short_forecast[:35]
                    text = f"{time_display:6}{temp_display:5}{short}"
                    period_surf = self.font(ctx, "normal").render(text, True, white)
                    surface.blit(period_surf, (65, y_pos))

        surface.set_clip(None)

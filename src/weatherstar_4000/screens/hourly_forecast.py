"""Hourly Forecast screen: continuously scrolling hour-by-hour listing."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen


@plugin
class HourlyForecastScreen(Screen):
    name = "hourly_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    layout = (
        ComponentSpec(component="background", config={"background_name": "4"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Hourly", "title_bottom": "Forecast", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        hourly = self.weather_data(ctx, "get_hourly") or {}
        try:
            periods = hourly.get("periods") or []
        except Exception:
            periods = []
        if not periods:
            forecast = self.weather_data(ctx, "get_forecast") or {}
            try:
                periods = forecast.get("periods") or []
            except Exception:
                periods = []

        yellow = self.color(ctx, "yellow")
        white = self.color(ctx, "white")

        if not periods:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        content_top = 125
        content_height = 265
        line_height = 25
        total_lines = len(periods[:24])
        total_content_height = total_lines * line_height

        scroll_time = pygame.time.get_ticks() // 50
        scroll_offset = scroll_time % (total_content_height + content_height)

        header_surf = self.font(ctx, "small").render("TIME  TEMP  CONDITIONS", True, yellow)
        surface.blit(header_surf, (65, content_top))

        clip_rect = pygame.Rect(0, content_top + 30, 640, content_height)
        surface.set_clip(clip_rect)

        base_y = content_top + 30 + content_height - scroll_offset
        for loop in range(2):
            y_offset = loop * total_content_height
            for i, period in enumerate(periods[:24]):
                y_pos = base_y + y_offset + (i * line_height)
                if content_top <= y_pos <= content_top + content_height + 50:
                    start_time = period.get("startTime")
                    time_display = ""
                    if start_time:
                        try:
                            hour_time = datetime.fromisoformat(
                                str(start_time).replace("Z", "+00:00")
                            )
                            time_display = hour_time.strftime("%I %p").lstrip("0").rjust(7)
                        except (ValueError, TypeError):
                            time_display = ""
                    if not time_display:
                        time_display = str(period.get("name", ""))[:7].rjust(7)

                    temp = period.get("temperature")
                    if temp is None:
                        temp = 0
                    temp_display = f"{int(temp):3}\N{DEGREE SIGN}"

                    short = str(period.get("shortForecast", ""))[:35]
                    text = f"{time_display:6}{temp_display:5}{short}"
                    period_surf = self.font(ctx, "normal").render(text, True, white)
                    surface.blit(period_surf, (65, y_pos))

        surface.set_clip(None)

"""Local Forecast screen: three-day column layout with wrapped text."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen


@plugin
class LocalForecastScreen(Screen):
    name = "local_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    layout = (
        ComponentSpec(component="background", config={"background_name": "2"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Local", "title_bottom": "Forecast", "has_noaa": True},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        forecast = self.weather_data(ctx, "get_forecast") or {}
        try:
            periods = forecast.get("periods") or []
        except Exception:
            periods = []

        if len(periods) < 3:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        yellow = self.color(ctx, "yellow")
        white = self.color(ctx, "white")
        total_width = 640
        col_width = 180
        col_spacing = 30
        total_cols_width = (col_width * 3) + (col_spacing * 2)
        start_x = (total_width - total_cols_width) // 2
        columns = [
            start_x + 10,
            start_x + col_width + col_spacing,
            start_x + (col_width + col_spacing) * 2 - 10,
        ]

        for col_idx, period in enumerate(periods[:3]):
            col_x = columns[col_idx]
            center_x = col_x + col_width // 2
            name = str(period.get("name", ""))

            if col_idx == 0:
                if "Tonight" in name or "Overnight" in name or "Night" in name.split()[-1]:
                    display_name = "TONIGHT"
                else:
                    display_name = "TODAY"
            elif col_idx == 1:
                display_name = "TOMORROW"
            else:
                day_name = (
                    name.replace(" Night", "").replace(" Afternoon", "").replace(" Morning", "")
                )
                display_name = day_name.upper()[:9]

            name_surf = self.font(ctx, "extended").render(display_name, True, yellow)
            surface.blit(name_surf, name_surf.get_rect(center=(center_x, 120)))

            temp = period.get("temperature")
            if temp is not None:
                temp_surf = self.font(ctx, "normal").render(f"{temp}\N{DEGREE SIGN}", True, white)
                surface.blit(temp_surf, temp_surf.get_rect(center=(center_x, 150)))

            try:
                detailed = period.get("detailedForecast") or ""
            except Exception:
                detailed = ""
            lines = self.wrap(self.font(ctx, "forecast"), str(detailed), col_width - 20)

            y_pos = 180
            for line in lines[:10]:
                text_surf = self.font(ctx, "forecast").render(line, True, white)
                surface.blit(text_surf, text_surf.get_rect(center=(center_x, y_pos)))
                y_pos += 18

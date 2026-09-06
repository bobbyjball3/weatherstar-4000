"""Weekend Forecast screen: Saturday and Sunday columns."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.datasources.noaa import ForecastPeriod
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen


@plugin
class WeekendForecastScreen(Screen):
    name = "weekend_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    def _draw_day_column(
        self,
        surface: pygame.Surface,
        ctx: Any,
        col_x: int,
        title: str,
        periods: list[ForecastPeriod],
    ) -> None:
        yellow = self.color(ctx, "yellow")
        cyan = self.color(ctx, "cyan")
        white = self.color(ctx, "white")
        col_width = 260

        y_pos = 145
        title_surf = self.font(ctx, "extended").render(title, True, yellow)
        surface.blit(title_surf, title_surf.get_rect(center=(col_x + col_width // 2, y_pos)))
        y_pos += 35

        for period in periods[:2]:
            name = period.name
            time_of_day = "DAY" if "Day" in name or "Night" not in name else "NIGHT"
            tod_surf = self.font(ctx, "normal").render(time_of_day, True, cyan)
            surface.blit(tod_surf, (col_x + 10, y_pos))
            y_pos += 25

            temp = period.temperature
            if temp is not None:
                temp_surf = self.font(ctx, "normal").render(
                    f"{int(temp)}\N{DEGREE SIGN}", True, white
                )
                surface.blit(temp_surf, (col_x + 10, y_pos))
            y_pos += 25

            icon = self.icon_surface(ctx, self.icon_name(period.icon))
            if icon is not None:
                orig_size = icon.get_size()
                if orig_size[0] > 0 and orig_size[1] > 0:
                    scale_factor = min(60 / orig_size[0], 60 / orig_size[1])
                    new_size = (int(orig_size[0] * scale_factor), int(orig_size[1] * scale_factor))
                    scaled = pygame.transform.scale(icon, new_size)
                    icon_x = col_x + 70 + (60 - new_size[0]) // 2
                    icon_y = y_pos - 50 + (60 - new_size[1]) // 2
                    surface.blit(scaled, (icon_x, icon_y))

            short = period.short_forecast
            lines = self.wrap(self.font(ctx, "tiny"), short, col_width - 20)
            for line in lines[:3]:
                line_surf = self.font(ctx, "tiny").render(line, True, white)
                surface.blit(line_surf, (col_x + 10, y_pos))
                y_pos += 18

            y_pos += 15

    layout = (
        ComponentSpec(component="background", config={"background_name": "4"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Weekend", "title_bottom": "Forecast", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        periods: list[ForecastPeriod] = self.weather_data(ctx, "get_forecast") or []

        left_col_x = 60
        right_col_x = 340
        saturday_periods: list[ForecastPeriod] = []
        sunday_periods: list[ForecastPeriod] = []

        for period in periods:
            name = period.name
            if "Saturday" in name:
                saturday_periods.append(period)
            elif "Sunday" in name:
                sunday_periods.append(period)
            if len(saturday_periods) >= 2 and len(sunday_periods) >= 2:
                break

        if saturday_periods:
            self._draw_day_column(surface, ctx, left_col_x, "SATURDAY", saturday_periods)
        if sunday_periods:
            self._draw_day_column(surface, ctx, right_col_x, "SUNDAY", sunday_periods)

        if not saturday_periods and not sunday_periods:
            msg = self.font(ctx, "normal").render(
                "Weekend forecast not available", True, self.color(ctx, "white")
            )
            surface.blit(msg, msg.get_rect(center=(320, 240)))

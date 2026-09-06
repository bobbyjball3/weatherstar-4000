"""Extended Forecast screen: three day/night columns with hi/lo temps."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.datasources.noaa import ForecastPeriod
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen


@plugin
class ExtendedForecastScreen(Screen):
    name = "extended_forecast"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)

    layout = (
        ComponentSpec(component="background", config={"background_name": "3"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Extended", "title_bottom": "Forecast", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        periods: list[ForecastPeriod] = self.weather_data(ctx, "get_forecast") or []

        day_width = 155
        total_width = 640
        num_days = min(3, len(periods) // 2)

        if num_days == 0:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        total_column_width = day_width * num_days
        remaining_space = total_width - total_column_width
        side_margin = remaining_space // (num_days + 1)
        start_x = side_margin

        yellow = self.color(ctx, "yellow")
        white = self.color(ctx, "white")
        blue = self.color(ctx, "blue")
        day_count = 0

        for i in range(0, min(len(periods), 6), 2):
            if day_count >= 3:
                break
            day_period = periods[i]
            night_period = periods[i + 1] if i + 1 < len(periods) else None

            x_pos = start_x + (day_count * (day_width + side_margin))
            col_center = x_pos + day_width // 2

            day_name = self._day_label(day_period, night_period)
            if day_name:
                name_surf = self.font(ctx, "extended").render(day_name, True, yellow)
                surface.blit(name_surf, name_surf.get_rect(center=(col_center, 120)))

            original_icon = self.icon_surface(ctx, self.icon_name(day_period.icon))
            if original_icon is not None:
                orig_w, orig_h = original_icon.get_size()
                if orig_h > 0:
                    scale = 75 / orig_h
                    new_w = int(orig_w * scale)
                    new_h = 75
                    if new_w > 100 and orig_w > 0:
                        scale = 100 / orig_w
                        new_w = 100
                        new_h = int(orig_h * scale)
                else:
                    new_w, new_h = 86, 75
                icon = pygame.transform.scale(original_icon, (new_w, new_h))
                surface.blit(icon, icon.get_rect(center=(col_center, 180)))

            short_forecast = day_period.short_forecast
            lines = self.wrap(self.font(ctx, "small"), short_forecast, day_width - 10)

            cond_y = 240
            for line in lines[:2]:
                cond_surf = self.font(ctx, "small").render(line, True, white)
                surface.blit(cond_surf, cond_surf.get_rect(center=(col_center, cond_y)))
                cond_y += 25

            if day_period.is_daytime:
                hi_temp = day_period.temperature
                lo_temp = night_period.temperature if night_period else None
            else:
                lo_temp = day_period.temperature
                hi_temp = (
                    night_period.temperature if night_period and night_period.is_daytime else None
                )

            temp_block_width = int(day_width * 0.44)
            lo_x_center = x_pos + temp_block_width // 2 + 10
            if lo_temp is not None:
                lo_label = self.font(ctx, "small").render("Lo", True, blue)
                surface.blit(lo_label, lo_label.get_rect(center=(lo_x_center, 310)))
                lo_surf = self.font(ctx, "normal").render(
                    f"{int(lo_temp)}\N{DEGREE SIGN}", True, white
                )
                surface.blit(lo_surf, lo_surf.get_rect(center=(lo_x_center, 335)))

            hi_x_center = x_pos + day_width - temp_block_width // 2 - 10
            if hi_temp is not None:
                hi_label = self.font(ctx, "small").render("Hi", True, yellow)
                surface.blit(hi_label, hi_label.get_rect(center=(hi_x_center, 310)))
                hi_surf = self.font(ctx, "normal").render(
                    f"{int(hi_temp)}\N{DEGREE SIGN}", True, white
                )
                surface.blit(hi_surf, hi_surf.get_rect(center=(hi_x_center, 335)))

            day_count += 1

    def _day_label(self, day_period: ForecastPeriod, night_period: ForecastPeriod | None) -> str:
        """Weekday abbreviation for a day/night column (e.g. SAT, SUN, MON)."""
        for period in (day_period, night_period):
            if period and period.is_daytime:
                return period.weekday_abbrev()
        return (day_period or night_period).weekday_abbrev()

    def _weekday_abbrev(self, period: ForecastPeriod) -> str:
        """Weekday abbreviation for a period (e.g. SAT, SUN, MON)."""
        return period.weekday_abbrev()

"""Weather Hazards screen: keyword scan of the forecast, with safety tips."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.datasources.noaa import ForecastPeriod
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen

#: Keywords that flag a forecast period as hazardous (legacy scan set).
_HAZARD_WORDS = ("storm", "severe", "warning", "watch", "advisory")

#: Fallback tips shown when no hazard is detected.
_SAFETY_TIPS = (
    "\u2022 Monitor weather conditions regularly",
    "\u2022 Have an emergency kit prepared",
    "\u2022 Know your evacuation routes",
    "\u2022 Sign up for weather alerts",
)


@plugin
class HazardsScreen(Screen):
    name = "hazards"
    media = ("backgrounds", "fonts", "logos")
    datasources = ("weather",)

    layout = (
        ComponentSpec(component="background", config={"background_name": "3"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Weather", "title_bottom": "Alerts", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        if self.variant(ctx) == "3000":
            self._compose_3000(surface, ctx)
            return
        white = self.color(ctx, "white", (255, 255, 255))
        yellow = self.color(ctx, "yellow", (255, 255, 0))
        normal = self.font(ctx, "normal")
        extended = self.font(ctx, "extended")

        y_pos = 175
        title = extended.render("CURRENT HAZARDS", True, yellow)
        surface.blit(title, (60, y_pos))
        y_pos += 40

        periods = self._forecast_periods(ctx)
        has_alerts = False

        for period in periods[:3]:
            forecast_text = period.detailed_forecast.lower()
            if not any(word in forecast_text for word in _HAZARD_WORDS):
                continue
            has_alerts = True
            name = period.name
            name_text = normal.render(f"{name}:", True, yellow)
            surface.blit(name_text, (80, y_pos))
            y_pos += 25

            words = period.short_forecast.split()
            line: list[str] = []
            for word in words:
                line.append(word)
                if normal.size(" ".join(line))[0] <= 480:
                    continue
                line.pop()
                if line:
                    text_surf = normal.render(" ".join(line), True, white)
                    surface.blit(text_surf, (100, y_pos))
                    y_pos += 25
                line = [word]
            if line:
                text_surf = normal.render(" ".join(line), True, white)
                surface.blit(text_surf, (100, y_pos))
                y_pos += 35

        if not has_alerts:
            no_alert = normal.render("No active weather alerts at this time", True, white)
            surface.blit(no_alert, no_alert.get_rect(center=(320, 230)))

            y_pos = 290
            tips_title = extended.render("WEATHER SAFETY TIPS", True, yellow)
            surface.blit(tips_title, (60, y_pos))
            y_pos += 35
            for tip in _SAFETY_TIPS:
                surface.blit(normal.render(tip, True, white), (80, y_pos))
                y_pos += 25

    # -- WeatherStar 3000 (ws3kp) variant ------------------------------------

    def _compose_3000(self, surface: pygame.Surface, ctx: Any) -> None:
        """ws3kp Hazards: a full-height dark-red box of uppercase hazard text.

        No header.  Each matching forecast hazard is centered in the box between
        80px margins (see _hazards.scss), white on ``hazard_bg``.
        """
        white = self.color(ctx, "white", (255, 255, 255))
        hazard_bg = self.color(ctx, "hazard_bg", (112, 35, 35))
        box = pygame.Rect(0, 0, surface.get_width(), 410)
        surface.fill(hazard_bg, box)

        font = self.font(ctx, "large")
        left = 80
        right = surface.get_width() - 80
        y_pos = 110
        row_step = 40

        periods = self._forecast_periods(ctx)
        drawn = False
        for period in periods[:3]:
            forecast_text = period.detailed_forecast.lower()
            if not any(word in forecast_text for word in _HAZARD_WORDS):
                continue
            drawn = True
            text = f"{period.name}. {period.short_forecast}".upper()
            for line in self.wrap(font, text, right - left):
                self.draw_text(surface, ctx, line, (left, y_pos), font_name="large", color=white)
                y_pos += row_step
                if y_pos > 380:
                    break
            if y_pos > 380:
                break

        if not drawn:
            text = "NO ACTIVE WEATHER ALERTS AT THIS TIME".upper()
            rect = font.render(text, True, white).get_rect(center=(320, 200))
            self.draw_text(surface, ctx, text, rect, font_name="large", color=white)

    def _forecast_periods(self, ctx: Any) -> list[ForecastPeriod]:
        return self.weather_data(ctx, "get_forecast") or []

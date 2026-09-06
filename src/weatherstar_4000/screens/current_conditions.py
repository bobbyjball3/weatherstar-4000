"""Current Conditions screen: big temperature, icon, wind, observation rows."""

from __future__ import annotations

from typing import Any

import pygame
from pydantic import PrivateAttr

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.datasources.noaa import CurrentConditions
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen


@plugin
class CurrentConditionsScreen(Screen):
    name = "current_conditions"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)
    _pressure_history: list | None = PrivateAttr(default=None)

    layout = (
        ComponentSpec(component="background", config={"background_name": "1"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Current", "title_bottom": "Conditions", "has_noaa": True},
        ),
        ComponentSpec(component="clock"),
    )

    def _city_state(self, ctx: Any) -> tuple[str, str]:
        loc = getattr(ctx, "location", None)
        if loc is None:
            return "", ""
        try:
            city = self.datasource(ctx, "weather").get_city(loc.lat, loc.lon)
        except Exception:  # noqa: BLE001 - fall back to the configured label
            return "", ""
        return city.city or "", city.state or ""

    def _city_desc(self, ctx: Any) -> str:
        loc = getattr(ctx, "location", None)
        if loc is None:
            return ""
        return (getattr(loc, "description", "") or "") if loc is not None else ""

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        current: CurrentConditions | None = self.weather_data(ctx, "get_current")
        if current is None:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        content_left = 64
        left_col_center = content_left + 127
        white = self.color(ctx, "white")
        yellow = self.color(ctx, "yellow")

        temp_f = current.temperature_f
        if temp_f is not None:
            temp_surf = self.font(ctx, "large").render(f"{temp_f}\N{DEGREE SIGN}", True, white)
            surface.blit(temp_surf, temp_surf.get_rect(center=(left_col_center, 140)))

        description = current.text_description[:15]
        if description:
            desc_surf = self.font(ctx, "extended").render(description, True, white)
            surface.blit(desc_surf, desc_surf.get_rect(center=(left_col_center, 190)))

        icon = self.icon_surface(ctx, self.icon_name(current.icon_url), 86, 75)
        if icon is not None:
            surface.blit(icon, icon.get_rect(center=(left_col_center, 260)))

        wind_y = 320
        wind_label = self.font(ctx, "extended").render("Wind:", True, white)
        surface.blit(wind_label, (content_left + 10, wind_y))

        wind_mph = current.wind_mph
        if wind_mph is not None and wind_mph > 0:
            direction = self.cardinal(current.wind_direction)
            wind_str = f"{direction} {int(round(wind_mph))}".strip()
        elif wind_mph is not None and wind_mph == 0:
            wind_str = "Calm"
        else:
            wind_str = "N/A"

        wind_text = self.font(ctx, "extended").render(wind_str, True, white)
        surface.blit(wind_text, wind_text.get_rect(right=content_left + 245, y=wind_y))

        wind_gust_mph = current.wind_gust_mph
        if wind_gust_mph is not None:
            gust_text = self.font(ctx, "normal").render(
                f"Gusts to {int(round(wind_gust_mph))}", True, white
            )
            surface.blit(gust_text, gust_text.get_rect(right=content_left + 245, y=wind_y + 35))

        right_col_x = content_left + 257
        label_x = right_col_x + 20
        value_x = 640 - 64 - 10
        y_pos = 100

        city, state = self._city_state(ctx)
        if city:
            location_str = city if not state else f"{city}, {state}"
        else:
            location_str = self._city_desc(ctx)
        location_str = location_str.strip()[:20]
        if location_str:
            loc_surf = self.font(ctx, "normal").render(location_str, True, yellow)
            surface.blit(loc_surf, (right_col_x, y_pos))
            y_pos += 30

        pressure_trend = ""
        if current.pressure_inhg is not None:
            history = self._pressure_history
            if history is None:
                history = []
                self._pressure_history = history
            history.append(current.pressure_inhg)
            if len(history) > 5:
                history.pop(0)
            if len(history) >= 2:
                change = history[-1] - history[0]
                if change > 0.02:
                    pressure_trend = "\u2191"
                elif change < -0.02:
                    pressure_trend = "\u2193"
                else:
                    pressure_trend = "\u2192"

        for label, value in current.observation_rows(pressure_trend):
            label_surf = self.font(ctx, "normal").render(label, True, white)
            surface.blit(label_surf, (label_x, y_pos))
            value_surf = self.font(ctx, "normal").render(value, True, white)
            surface.blit(value_surf, value_surf.get_rect(right=value_x, y=y_pos))
            y_pos += 36

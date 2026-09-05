"""Current Conditions screen: big temperature, icon, wind, observation rows."""

from __future__ import annotations

from typing import Any

import pygame
from pydantic import PrivateAttr

from weatherstar_4000 import render
from weatherstar_4000.components.base import ComponentSpec
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
        desc = getattr(loc, "description", "") if loc is not None else ""
        ds = self.datasource(ctx, "weather")
        if ds is not None and hasattr(ds, "get_city") and loc is not None:
            try:
                lat, lon = self.latlon(ctx)
                city, state = ds.get_city(lat, lon)
                return (city or ""), (state or "")
            except Exception:
                pass
        return desc, ""

    def _city_desc(self, ctx: Any) -> str:
        loc = getattr(ctx, "location", None)
        return (getattr(loc, "description", "") or "") if loc is not None else ""

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        current = self.weather_data(ctx, "get_current") or {}
        if not current:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        content_left = 64
        left_col_center = content_left + 127
        white = self.color(ctx, "white")
        yellow = self.color(ctx, "yellow")

        temp_f = self.fahrenheit(self.num(current, "temperature"))
        if temp_f is not None:
            temp_surf = self.font(ctx, "large").render(f"{temp_f}\N{DEGREE SIGN}", True, white)
            surface.blit(temp_surf, temp_surf.get_rect(center=(left_col_center, 140)))

        description = self.text(current, "textDescription", 15)
        if description:
            desc_surf = self.font(ctx, "extended").render(description, True, white)
            surface.blit(desc_surf, desc_surf.get_rect(center=(left_col_center, 190)))

        icon = self.icon_surface(ctx, self.icon_name(self.text(current, "icon")), 86, 75)
        if icon is not None:
            surface.blit(icon, icon.get_rect(center=(left_col_center, 260)))

        wind_y = 320
        wind_speed = self.num(current, "windSpeed")
        wind_dir = self.num(current, "windDirection")
        wind_label = self.font(ctx, "extended").render("Wind:", True, white)
        surface.blit(wind_label, (content_left + 10, wind_y))

        if wind_speed is not None and wind_speed > 0:
            wind_mph = int(wind_speed * 0.621371)
            direction = self.cardinal(wind_dir)
            wind_str = f"{direction.ljust(3)}{str(wind_mph).rjust(3)}"
        elif wind_speed is not None and wind_speed == 0:
            wind_str = "Calm"
        else:
            wind_str = "N/A"

        wind_text = self.font(ctx, "extended").render(wind_str, True, white)
        surface.blit(wind_text, wind_text.get_rect(right=content_left + 245, y=wind_y))

        wind_gust = self.num(current, "windGust")
        if wind_gust is not None:
            gust_mph = int(wind_gust * 0.621371)
            gust_text = self.font(ctx, "normal").render(f"Gusts to {gust_mph}", True, white)
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

        row_data = []

        humidity = self.num(current, "relativeHumidity")
        if humidity is not None:
            row_data.append(("Humidity:", f"{int(humidity)}%"))

        dewpoint_f = self.fahrenheit(self.num(current, "dewpoint"))
        if dewpoint_f is not None:
            row_data.append(("Dewpoint:", f"{dewpoint_f}\N{DEGREE SIGN}"))

        cloud_layers = (current or {}).get("cloudLayers") or []
        if not isinstance(cloud_layers, list):
            cloud_layers = []
        ceiling = None
        for layer in cloud_layers:
            try:
                amount = layer.get("amount")
            except Exception:
                amount = None
            if amount in ("BKN", "OVC"):
                base = self.num(layer, "base")
                if base is not None:
                    ceiling = int(base * 3.28084)
                    break
        if ceiling is None or ceiling == 0:
            ceiling_str = "Unlimited"
        else:
            ceiling_str = f"{ceiling} ft"
        row_data.append(("Ceiling:", ceiling_str))

        visibility = self.num(current, "visibility")
        if visibility is not None:
            vis_miles = visibility * 0.000621371
            if vis_miles >= 10:
                vis_str = "10 mi"
            else:
                vis_str = f"{vis_miles:.1f} mi"
            row_data.append(("Visibility:", vis_str))

        pressure_value = self.num(current, "barometricPressure")
        if pressure_value is None:
            pressure_value = self.num(current, "pressure")
        if pressure_value is not None:
            pressure_inhg = pressure_value * 0.0002953
            history = getattr(self, "_pressure_history", None)
            if history is None:
                history = []
                self._pressure_history = history
            history.append(pressure_inhg)
            if len(history) > 5:
                history.pop(0)
            trend = ""
            if len(history) >= 2:
                change = history[-1] - history[0]
                if change > 0.02:
                    trend = "\u2191"
                elif change < -0.02:
                    trend = "\u2193"
                else:
                    trend = "\u2192"
            row_data.append(("Pressure:", f'{pressure_inhg:.2f}" {trend}'.strip()))

        temp_c = self.num(current, "temperature")
        heat_index = self.num(current, "heatIndex")
        wind_chill = self.num(current, "windChill")
        if heat_index is not None and temp_c is not None and temp_c > 26:
            heat_f = self.fahrenheit(heat_index)
            if heat_f is not None:
                row_data.append(("Heat Index:", f"{heat_f}\N{DEGREE SIGN}"))
        elif wind_chill is not None and temp_c is not None and temp_c < 10:
            chill_f = self.fahrenheit(wind_chill)
            if chill_f is not None:
                row_data.append(("Wind Chill:", f"{chill_f}\N{DEGREE SIGN}"))

        for label, value in row_data:
            label_surf = self.font(ctx, "normal").render(label, True, white)
            surface.blit(label_surf, (label_x, y_pos))
            value_surf = self.font(ctx, "normal").render(value, True, white)
            surface.blit(value_surf, value_surf.get_rect(right=value_x, y=y_pos))
            y_pos += 36

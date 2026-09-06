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
from weatherstar_4000.themes import LayoutVariant


@plugin
class CurrentConditionsScreen(Screen):
    name = "current_conditions"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)
    _pressure_history: list | None = PrivateAttr(default=None)

    variants = {
        LayoutVariant.WS4000: "compose_4000",
        LayoutVariant.WS3000: "compose_3000",
    }

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

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
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

    # -- WeatherStar 3000 (ws3kp) variant --------------------------------

    def compose_3000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        """ws3kp Current Conditions: a plain 8-line text list, 24pt on 40px rows.

        No header, no icon, no big temperature - just the observation text block
        mirrored from the ws3kp current-weather template, left aligned from the
        35px margin at a 40px top margin (see _current-weather.scss).
        """
        current: CurrentConditions | None = self.weather_data(ctx, "get_current")
        if current is None:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        white = self.color(ctx, "white")
        left = int(self.layout_token(ctx, "content_left", 35))
        top = int(self.layout_token(ctx, "content_top", 40))
        row_height = int(self.layout_token(ctx, "row_height", 40))

        city, state = self._city_state(ctx)
        if city:
            location_str = city if not state else f"{city}, {state}"
        else:
            location_str = self._city_desc(ctx)
        location_str = location_str.strip()[:20]

        lines: list[str] = []
        if location_str:
            lines.append(f"Conditions at {location_str}")

        condition = self._short_condition(current.text_description)
        if condition:
            lines.append(condition)

        degree = "\N{DEGREE SIGN}"
        temp_f = current.temperature_f
        if temp_f is not None:
            lines.append(f"Temperature: {temp_f}{degree}")

        humidity = current.relative_humidity
        dewpoint_f = current.dewpoint_f
        if humidity is not None or dewpoint_f is not None:
            left_part = f"Humidity: {int(humidity)}%" if humidity is not None else "Humidity:"
            right_part = f"Dewpoint: {dewpoint_f}{degree}" if dewpoint_f is not None else ""
            lines.append(f"{left_part}    {right_part}".rstrip())

        pressure = current.pressure_inhg
        if pressure is not None:
            lines.append(f"Barometric Pressure: {pressure:.2f} {self._trend_letter(ctx, pressure)}")

        wind_mph = current.wind_mph
        if wind_mph is not None:
            if wind_mph > 0:
                direction = self.cardinal(current.wind_direction)
                wind_str = f"{direction:<3}{int(wind_mph):>3}"
            else:
                wind_str = "Calm"
            lines.append(f"Wind: {wind_str}")

        visibility_miles = current.visibility_miles
        if visibility_miles is not None:
            vis = (
                f"{round(visibility_miles)}"
                if visibility_miles >= 10
                else f"{visibility_miles:.1f}"
            )
            ceiling = "Unlimited" if not current.ceiling_ft else f"{current.ceiling_ft} ft."
            lines.append(f"Visib: {vis} mi.  Ceiling: {ceiling}")

        if (
            current.heat_index_f is not None
            and current.temperature_c is not None
            and current.temperature_c > 26
        ):
            lines.append(f"Heat Index: {current.heat_index_f}{degree}")
        elif (
            current.wind_chill_f is not None
            and current.temperature_c is not None
            and current.temperature_c < 10
        ):
            lines.append(f"Wind Chill: {current.wind_chill_f}{degree}")

        max_right = surface.get_width() - left - 8
        y = top
        for line in lines:
            slot = "large"
            if self.font(ctx, slot).size(line)[0] > max_right:
                slot = "extended"
            self.draw_text(surface, ctx, line, (left, y), font_name=slot, color=white)
            y += row_height

    def _trend_letter(self, ctx: Any, pressure_inhg: float) -> str:
        """ws3kp pressure trend letters: 'R' rising / 'F' falling (~150 Pa).

        The app re-renders from a single snapshot per frame, so trend is read
        from the same short inHg history the classic layout keeps.
        """
        history = self._pressure_history
        if history is None:
            history = []
            self._pressure_history = history
        history.append(pressure_inhg)
        if len(history) > 5:
            history.pop(0)
        if len(history) < 2:
            return ""
        change = history[-1] - history[0]
        if change > 0.044:
            return "R"
        if change < -0.044:
            return "F"
        return ""

    @staticmethod
    def _short_condition(condition: str) -> str:
        """ws3kp shortConditions(): abbreviate wordy NWS descriptions."""
        if len(condition) <= 15:
            return condition
        text = condition
        for long, short in (
            ("Freezing Rain", "Frz Rn"),
            ("Thunderstorm", "T'storm"),
            ("Freezing", "Frz"),
            ("Light", "L"),
            ("Heavy", "H"),
            ("Partly", "P"),
            ("Mostly", "M"),
            ("Few", "F"),
            ("Vicinity", ""),
        ):
            text = text.replace(long, short)
        text = text.replace(" in ", " ")
        text = text.replace(" and ", " ")
        text = text.replace(" with ", "/")
        return text

"""Current Conditions screen: big temperature, icon, wind, observation rows."""

from __future__ import annotations

from typing import Any

import pygame
from pydantic import PrivateAttr

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

_FONT_SIZES = {
    "title": 32,
    "large": 32,
    "extended": 32,
    "small": 28,
    "normal": 20,
    "forecast": 24,
    "tiny": 16,
    "scroller": 24,
}


def _ensure_fonts(ctx: Any) -> None:
    fonts = getattr(ctx, "fonts", None)
    if not isinstance(fonts, dict):
        return
    for name, size in _FONT_SIZES.items():
        fonts.setdefault(name, pygame.font.Font(None, size))


def _font(ctx: Any, name: str) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None)
    if isinstance(fonts, dict):
        found = fonts.get(name)
        if found is not None:
            return found
    return pygame.font.Font(None, _FONT_SIZES.get(name, 20))


def _color(
    ctx: Any, key: str, fallback: tuple[int, int, int] = (255, 255, 255)
) -> tuple[int, int, int]:
    try:
        return (ctx.colors or {}).get(key, fallback)
    except Exception:
        return fallback


def _num(props: Any, key: str) -> float | None:
    try:
        return (props or {}).get(key, {}).get("value")
    except Exception:
        return None


def _text(props: Any, key: str, maxlen: int | None = None) -> str:
    try:
        val = (props or {}).get(key, "")
        if isinstance(val, list):
            val = " ".join(str(part) for part in val if part)
        if not isinstance(val, str):
            val = str(val)
        return val if maxlen is None else val[:maxlen]
    except Exception:
        return ""


def _fahrenheit(celsius: float | None) -> int | None:
    if celsius is None:
        return None
    try:
        return int(celsius * 9 / 5 + 32)
    except Exception:
        return None


def _weather(ctx: Any) -> Any:
    try:
        return ctx.data.get("weather")
    except Exception:
        return None


def _data(ctx: Any, method: str) -> Any:
    ds = _weather(ctx)
    if ds is None:
        return None
    fn = getattr(ds, method, None)
    loc = getattr(ctx, "location", None)
    if fn is None or loc is None:
        return None
    try:
        return fn(loc.lat, loc.lon)
    except Exception:
        return None


def _city_state(ctx: Any) -> tuple[str, str]:
    loc = getattr(ctx, "location", None)
    desc = getattr(loc, "description", "") if loc is not None else ""
    ds = _weather(ctx)
    if ds is not None and hasattr(ds, "get_city") and loc is not None:
        try:
            city, state = ds.get_city(loc.lat, loc.lon)
            return (city or ""), (state or "")
        except Exception:
            pass
    return desc, ""


def _city_desc(ctx: Any) -> str:
    loc = getattr(ctx, "location", None)
    return (getattr(loc, "description", "") or "") if loc is not None else ""


def _icon_name(icon_url: str) -> str | None:
    if not icon_url:
        return None
    parts = icon_url.split("/")
    if len(parts) >= 2:
        condition = parts[-1].split("?")[0]
        icon_map = {
            "skc": "Clear",
            "few": "Clear",
            "sct": "Partly-Cloudy",
            "bkn": "Cloudy",
            "ovc": "Cloudy",
            "rain": "Rain",
            "rain_showers": "Shower",
            "tsra": "Thunderstorm",
            "snow": "Light-Snow",
            "fog": "Fog",
            "wind": "Windy",
        }
        return icon_map.get(condition, "Clear")
    return None


def _icon_surface(
    ctx: Any, name: str | None, width: int | None = None, height: int | None = None
) -> Any:
    if not name:
        return None
    try:
        mgr = getattr(ctx, "icon_manager", None)
        if mgr is None:
            mgr = (ctx.assets or {}).get("icon_manager")
        if mgr is not None:
            if width and height:
                return mgr.get_icon(name, width, height)
            return mgr.get_icon(name)
    except Exception:
        pass
    try:
        icons = (ctx.assets or {}).get("icons") or {}
        surface = icons.get(name)
    except Exception:
        surface = None
    if surface is not None and width and height:
        try:
            return pygame.transform.scale(surface, (width, height))
        except Exception:
            return surface
    return surface


def _cardinal(degrees: float | None) -> str:
    if degrees is None:
        return ""
    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    try:
        index = int((degrees + 11.25) / 22.5) % 16
        return directions[index]
    except Exception:
        return ""


@plugin
class CurrentConditionsScreen(Screen):
    name = "current_conditions"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ("weather",)
    _pressure_history: list | None = PrivateAttr(default=None)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        _ensure_fonts(ctx)
        render.draw_background(surface, ctx, "1")
        render.draw_header(surface, ctx, "Current", "Conditions", has_noaa=True)

        current = _data(ctx, "get_current") or {}
        if not current:
            render.draw_centered_text(
                surface, ctx, "NO DATA AVAILABLE", 240, font_name="large", color_key="yellow"
            )
            return

        content_left = 64
        left_col_center = content_left + 127
        white = _color(ctx, "white")
        yellow = _color(ctx, "yellow")

        temp_f = _fahrenheit(_num(current, "temperature"))
        if temp_f is not None:
            temp_surf = _font(ctx, "large").render(f"{temp_f}\N{DEGREE SIGN}", True, white)
            surface.blit(temp_surf, temp_surf.get_rect(center=(left_col_center, 140)))

        description = _text(current, "textDescription", 15)
        if description:
            desc_surf = _font(ctx, "extended").render(description, True, white)
            surface.blit(desc_surf, desc_surf.get_rect(center=(left_col_center, 190)))

        icon = _icon_surface(ctx, _icon_name(_text(current, "icon")), 86, 75)
        if icon is not None:
            surface.blit(icon, icon.get_rect(center=(left_col_center, 260)))

        wind_y = 320
        wind_speed = _num(current, "windSpeed")
        wind_dir = _num(current, "windDirection")
        wind_label = _font(ctx, "extended").render("Wind:", True, white)
        surface.blit(wind_label, (content_left + 10, wind_y))

        if wind_speed is not None and wind_speed > 0:
            wind_mph = int(wind_speed * 0.621371)
            direction = _cardinal(wind_dir)
            wind_str = f"{direction.ljust(3)}{str(wind_mph).rjust(3)}"
        elif wind_speed is not None and wind_speed == 0:
            wind_str = "Calm"
        else:
            wind_str = "N/A"

        wind_text = _font(ctx, "extended").render(wind_str, True, white)
        surface.blit(wind_text, wind_text.get_rect(right=content_left + 245, y=wind_y))

        wind_gust = _num(current, "windGust")
        if wind_gust is not None:
            gust_mph = int(wind_gust * 0.621371)
            gust_text = _font(ctx, "normal").render(f"Gusts to {gust_mph}", True, white)
            surface.blit(gust_text, gust_text.get_rect(right=content_left + 245, y=wind_y + 35))

        right_col_x = content_left + 257
        label_x = right_col_x + 20
        value_x = 640 - 64 - 10
        y_pos = 100

        city, state = _city_state(ctx)
        if city:
            location_str = city if not state else f"{city}, {state}"
        else:
            location_str = _city_desc(ctx)
        location_str = location_str.strip()[:20]
        if location_str:
            loc_surf = _font(ctx, "normal").render(location_str, True, yellow)
            surface.blit(loc_surf, (right_col_x, y_pos))
            y_pos += 30

        row_data = []

        humidity = _num(current, "relativeHumidity")
        if humidity is not None:
            row_data.append(("Humidity:", f"{int(humidity)}%"))

        dewpoint_f = _fahrenheit(_num(current, "dewpoint"))
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
                base = _num(layer, "base")
                if base is not None:
                    ceiling = int(base * 3.28084)
                    break
        if ceiling is None or ceiling == 0:
            ceiling_str = "Unlimited"
        else:
            ceiling_str = f"{ceiling} ft"
        row_data.append(("Ceiling:", ceiling_str))

        visibility = _num(current, "visibility")
        if visibility is not None:
            vis_miles = visibility * 0.000621371
            if vis_miles >= 10:
                vis_str = "10 mi"
            else:
                vis_str = f"{vis_miles:.1f} mi"
            row_data.append(("Visibility:", vis_str))

        pressure_value = _num(current, "barometricPressure")
        if pressure_value is None:
            pressure_value = _num(current, "pressure")
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

        temp_c = _num(current, "temperature")
        heat_index = _num(current, "heatIndex")
        wind_chill = _num(current, "windChill")
        if heat_index is not None and temp_c is not None and temp_c > 26:
            heat_f = _fahrenheit(heat_index)
            if heat_f is not None:
                row_data.append(("Heat Index:", f"{heat_f}\N{DEGREE SIGN}"))
        elif wind_chill is not None and temp_c is not None and temp_c < 10:
            chill_f = _fahrenheit(wind_chill)
            if chill_f is not None:
                row_data.append(("Wind Chill:", f"{chill_f}\N{DEGREE SIGN}"))

        for label, value in row_data:
            label_surf = _font(ctx, "normal").render(label, True, white)
            surface.blit(label_surf, (label_x, y_pos))
            value_surf = _font(ctx, "normal").render(value, True, white)
            surface.blit(value_surf, value_surf.get_rect(right=value_x, y=y_pos))
            y_pos += 36

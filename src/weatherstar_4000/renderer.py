"""Shared rendering helpers for Screens and Components.

Screens and Components both draw onto a pygame surface using the shared
:class:`~weatherstar_4000.context.AppContext` (fonts, colors, assets,
datasources).  Historically every screen re-declared small module-level helpers
(``_font``, ``_color``, ``_ds``, ``_latlon``, ...) with slightly different
fallback semantics.  This mixin moves those concrete helpers onto the interface
so a Screen/Component just calls ``self.font(ctx, ...)`` / ``self.color(ctx,
...)``.

The mixin defines methods only: any plain class attribute here would be
inherited by Pydantic plugin models and rejected as a non-annotated attribute,
so constants live at module scope.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame

#: Fallback font sizes by name (mirrors media/fonts.py), used when the runtime
#: context has no loaded font for a key.
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

_WHITE = (255, 255, 255)
_YELLOW = (255, 255, 0)

#: The sixteen classic compass points, indexed by a heading in degrees.
_CARDINALS = [
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

#: NOAA condition token -> weather icon name (classic WeatherStar set).
_ICON_NAMES = {
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


class Renderer:
    """Concrete drawing/data helpers shared by Screens and Components.

    Every method is stateless and reads from the ``ctx`` argument so subclasses
    (Pydantic plugins) never need per-instance bookkeeping for these helpers.
    """

    # -- fonts / colors ---------------------------------------------------

    def font(self, ctx: Any, name: str = "normal") -> pygame.font.Font:
        """Return the named font, or a usable fallback (never ``None``).

        Prefers the named font, then any loaded font in ``ctx.fonts``, then an
        ad-hoc pygame default sized per ``name``.
        """
        fonts = getattr(ctx, "fonts", None)
        if isinstance(fonts, dict):
            found = fonts.get(name)
            if found is not None:
                return found
            if fonts:
                return next(iter(fonts.values()))
        return pygame.font.Font(None, _FONT_SIZES.get(name, 20))

    def color(
        self, ctx: Any, key: str, fallback: tuple[int, int, int] = _WHITE
    ) -> tuple[int, int, int]:
        """Return a theme color by key, or ``fallback`` when missing."""
        colors = getattr(ctx, "colors", None)
        if isinstance(colors, dict):
            return colors.get(key, fallback)
        return fallback

    def text_surface(
        self,
        ctx: Any,
        text: str,
        *,
        font_name: str = "normal",
        color_key: str = "white",
        color: tuple[int, int, int] | None = None,
    ) -> pygame.Surface:
        """Render ``text`` to a surface using a named font and color."""
        fg = color if color is not None else self.color(ctx, color_key)
        return self.font(ctx, font_name).render(text, True, fg)

    def blit_text(
        self,
        surface: pygame.Surface,
        ctx: Any,
        text: str,
        pos,
        *,
        font_name: str = "normal",
        color_key: str = "white",
        color: tuple[int, int, int] | None = None,
    ) -> pygame.Rect:
        """Render ``text`` at ``pos`` (a position or rect) and return its rect."""
        rendered = self.text_surface(
            ctx, text, font_name=font_name, color_key=color_key, color=color
        )
        return surface.blit(rendered, pos)

    # -- context / datasource access -------------------------------------

    def datasource(self, ctx: Any, name: str) -> Any:
        """Return a registered datasource by name, or ``None`` if unavailable."""
        data = getattr(ctx, "data", None)
        if data is None:
            return None
        try:
            return data.get(name)
        except Exception:  # noqa: BLE001 - optional datasource
            return None

    def latlon(self, ctx: Any) -> tuple[float, float]:
        """Return the active (lat, lon), or ``(0.0, 0.0)`` when not set."""
        location = getattr(ctx, "location", None)
        if location is None:
            return 0.0, 0.0
        try:
            return float(location.lat), float(location.lon)
        except (AttributeError, TypeError, ValueError):
            return 0.0, 0.0

    # -- layout helpers ---------------------------------------------------

    def wrap(self, font: pygame.font.Font, text: str, max_width: int) -> list[str]:
        """Greedy word-wrap ``text`` into lines no wider than ``max_width`` px."""
        lines: list[str] = []
        current = ""
        for word in str(text).split():
            candidate = f"{current} {word}".strip() if current else word
            if font.size(candidate)[0] > max_width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def centered(
        self,
        surface: pygame.Surface,
        ctx: Any,
        text: str,
        y: int,
        *,
        font_name: str = "small",
        color_key: str = "white",
        center_x: int | None = None,
    ) -> pygame.Rect:
        """Draw ``text`` centered horizontally at height ``y``; return its rect."""
        rendered = self.text_surface(ctx, text, font_name=font_name, color_key=color_key)
        width = surface.get_width() if center_x is None else 2 * center_x
        rect = rendered.get_rect(center=(width // 2, y))
        surface.blit(rendered, rect)
        return rect

    # -- value conversions ------------------------------------------------

    def fahrenheit(self, celsius: float | None) -> int | None:
        """Convert °C to °F; returns ``None`` for unusable input."""
        if celsius is None:
            return None
        try:
            return int(celsius * 9 / 5 + 32)
        except (TypeError, ValueError):
            return None

    def cardinal(self, degrees: float | None, default: str = "") -> str:
        """Compass point for a heading in degrees ('' when unusable)."""
        if degrees is None:
            return default
        try:
            index = int((degrees + 11.25) / 22.5) % 16
            return _CARDINALS[index]
        except (TypeError, ValueError):
            return default

    def format_date(self, date_str: Any, fmt: str = "%a %m/%d") -> str:
        """Format a ``YYYY-MM-DD`` string as a short date; pass through otherwise."""
        if not date_str:
            return ""
        try:
            return datetime.strptime(str(date_str), "%Y-%m-%d").strftime(fmt)
        except (TypeError, ValueError):
            return str(date_str)

    # -- weather observation payload access --------------------------------

    def num(self, props: Any, key: str) -> float | None:
        """Return a NOAA quantity ``{"value": ...}`` as a float (or ``None``)."""
        try:
            return (props or {}).get(key, {}).get("value")
        except AttributeError:
            return None

    def measure(self, current: dict, *keys: str) -> float | None:
        """Return the first present numeric value for any of ``keys``.

        Accepts either NOAA ``{"value": ...}`` dicts or bare scalars.
        """
        for key in keys:
            raw = (current or {}).get(key)
            if raw is None:
                continue
            if isinstance(raw, dict):
                value = raw.get("value")
            else:
                value = raw
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    def text(self, props: Any, key: str, maxlen: int | None = None) -> str:
        """Return a NOAA observation text field as a string (optionally clipped)."""
        try:
            val = (props or {}).get(key, "")
            if isinstance(val, list):
                val = " ".join(str(part) for part in val if part)
            if not isinstance(val, str):
                val = str(val)
        except AttributeError:
            val = ""
        return val if maxlen is None else val[:maxlen]

    def weather_data(self, ctx: Any, method: str) -> Any:
        """Call ``weather.<method>(lat, lon)`` when available; else ``None``."""
        ds = self.datasource(ctx, "weather")
        fn = getattr(ds, method, None) if ds is not None else None
        if fn is None:
            return None
        location = getattr(ctx, "location", None)
        if location is None:
            return None
        try:
            return fn(location.lat, location.lon)
        except Exception:  # noqa: BLE001 - weather data is optional
            return None

    # -- weather icons -----------------------------------------------------

    @staticmethod
    def icon_name(icon_url: str) -> str | None:
        """Map a NOAA icon URL's condition token to a named icon."""
        if not icon_url:
            return None
        parts = icon_url.split("/")
        if len(parts) >= 2:
            condition = parts[-1].split("?")[0]
            return _ICON_NAMES.get(condition, "Clear")
        return None

    def icon_surface(
        self,
        ctx: Any,
        name: str | None,
        width: int | None = None,
        height: int | None = None,
    ) -> Any:
        """Resolve a named weather icon (icon manager, else asset dict)."""
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
        except Exception:  # noqa: BLE001 - fall back to asset dict
            pass
        try:
            surface = ((ctx.assets or {}).get("icons") or {}).get(name)
        except AttributeError:
            return None
        if surface is not None and width and height:
            try:
                return pygame.transform.scale(surface, (width, height))
            except Exception:  # noqa: BLE001 - return unscaled
                return surface
        return surface

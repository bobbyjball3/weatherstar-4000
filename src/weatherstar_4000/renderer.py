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
#: Exact tokens are tried first; see ``_icon_for_token`` for the fallback
#: classification of compound tokens (e.g. ``tsra_hi,40``).  Clear-sky tokens
#: are intentionally absent so the classifier can pick the day "Sunny" vs the
#: night "Clear" icon from the URL's day/night segment.
_ICON_NAMES = {
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


def _icon_for_token(token: str, night: bool = False) -> str | None:
    """Classify a NOAA icon token into a named weather icon (or ``None``).

    NOAA forecast icons carry coverage/intensity suffixes the classic set has
    no asset for (``tsra_hi,40``, ``tsra_sct,50``, ``nsct`` ...).  Substring
    classification keeps those pointing at the nearest available icon instead of
    collapsing every unknown condition onto a single default.
    """
    t = token.lower()
    if t in _ICON_NAMES:
        return _ICON_NAMES[t]
    if "tsra" in t or "thunder" in t or "tstm" in t or "tstorm" in t:
        return "Thunderstorm"
    if "blizzard" in t:
        return "Heavy-Snow"
    if "fzra" in t or "freezing" in t:
        if "sleet" in t:
            return "Freezing-Rain-Sleet"
        if "snow" in t:
            return "Freezing-Rain-Snow"
        return "Freezing-Rain"
    if "snow" in t:
        if "rain" in t:
            return "Snow-to-Rain"
        if "heavy" in t:
            return "Heavy-Snow"
        if "sleet" in t:
            return "Snow-Sleet"
        if "shower" in t or "shra" in t:
            return "Scattered-Snow-Showers"
        return "Light-Snow"
    if "sleet" in t or t in ("ip", "mix"):
        return "Sleet"
    if "smoke" in t or "dust" in t or t in ("du", "fu"):
        return "Smoke"
    if "wind" in t:
        return "Windy"
    if "fog" in t or t == "br":
        return "Fog"
    if "rain" in t or "shower" in t or "shra" in t or t == "ra":
        if "snow" in t or "sleet" in t:
            return "Rain-Snow"
        if "shower" in t or "shra" in t:
            return "Shower"
        return "Rain"
    if "clear" in t or "sunny" in t or t in ("skc", "few", "fair"):
        # Classic set distinguishes the day sun from the night clear sky.
        return "Clear" if night else "Sunny"
    if "partly" in t or "sct" in t:
        return "Partly-Cloudy"
    if "cloudy" in t or t in ("bkn", "ovc", "overcast"):
        return "Cloudy"
    return None


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
        """Return a registered datasource by name (strict).

        Screens/components reference datasources through their declared
        ``datasources`` tuples, so a missing name is a programming error: fail
        loudly (KeyError) instead of silently degrading to "no data".
        """
        data = getattr(ctx, "data", None)
        if data is None:
            raise KeyError(f"No datasource registry on ctx; cannot resolve {name!r}.")
        return data.get(name)

    def optional_datasource(self, ctx: Any, name: str) -> Any:
        """Like :meth:`datasource` but returns ``None`` when the name is absent.

        For genuinely optional reads (e.g. the always-on bottom ticker probing
        for weather) where a missing source is a normal condition.
        """
        try:
            return self.datasource(ctx, name)
        except KeyError:
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

    # -- weather data access -------------------------------------------------

    def weather_data(self, ctx: Any, method: str) -> Any:
        """Call ``weather.<method>(lat, lon)`` for the active location.

        Returns whatever the datasource method returns (a typed model, list, or
        ``None``).  Raises if no ``weather`` datasource is registered; weather
        screens declare it via their ``datasources`` tuple.
        """
        ds = self.datasource(ctx, "weather")
        fn = getattr(ds, method, None)
        if fn is None:
            return None
        location = getattr(ctx, "location", None)
        if location is None:
            return None
        return fn(location.lat, location.lon)

    # -- weather icons -----------------------------------------------------

    @staticmethod
    def icon_name(icon_url: str) -> str | None:
        """Map a NOAA icon URL's condition token to a named icon."""
        if not icon_url:
            return None
        parts = icon_url.split("/")
        if len(parts) >= 2:
            token = parts[-1].split("?")[0].split(",")[0]
            night = "night" in parts[-2].lower() if len(parts) >= 2 else False
            return _icon_for_token(token, night=night)
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

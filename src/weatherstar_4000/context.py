"""Runtime context shared by Screens and Components.

Replaces the legacy monolithic ``ws`` object.  The context carries the render
surface, resolved theme, named fonts/assets, and a :class:`DataRegistry` of
configured datasources so rendering code never reaches into a god object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

from weatherstar_4000.themes import BASE_COLORS, FALLBACK_THEME, Theme


@dataclass
class Location:
    """Geographic location used to drive weather datasources."""

    lat: float
    lon: float
    description: str = ""


class DataRegistry:
    """Named registry of configured Datasource instances."""

    def __init__(self) -> None:
        self._sources: dict[str, Any] = {}

    def register(self, name: str, datasource: Any) -> None:
        self._sources[name] = datasource

    def get(self, name: str) -> Any:
        try:
            return self._sources[name]
        except KeyError:
            raise KeyError(
                f"No datasource registered as {name!r}. "
                f"Registered: {', '.join(sorted(self._sources)) or '(none)'}"
            ) from None

    def names(self) -> list[str]:
        return sorted(self._sources)

    def clear(self) -> None:
        self._sources.clear()


class AppContext:
    """Shared, immutable-in-use rendering context for one run.

    The engine fills in ``surface``, ``theme``, ``fonts``, ``assets``, and the
    ``data`` registry before the sequence starts; Screens/Components read from
    it and never mutate it.
    """

    def __init__(
        self,
        surface: pygame.Surface | None = None,
        *,
        theme: Theme | None = None,
        fonts: dict[str, pygame.font.Font] | None = None,
        assets: dict[str, Any] | None = None,
        data: DataRegistry | None = None,
        icon_manager: Any = None,
        location: Location | None = None,
        active_screen: str | None = None,
    ):
        self.surface = surface
        self.theme = theme or FALLBACK_THEME
        self.fonts: dict[str, pygame.font.Font] = fonts or {}
        self.assets: dict[str, Any] = assets or {}
        self.data = data or DataRegistry()
        self.icon_manager = icon_manager
        self.location = location
        self.active_screen = active_screen

    # -- conveniences -------------------------------------------------------

    def get_color(self, key: str) -> tuple[int, int, int]:
        return self.colors.get(key, (255, 255, 255))

    @property
    def colors(self) -> dict[str, tuple[int, int, int]]:
        """Theme colors merged over the minimal base palette.

        Guarantees stable values for the keys renderers read directly
        (``BASE_COLORS``) while letting the configured theme override or add to
        them, so a partial theme palette never KeyErrors at render time.
        """
        merged = dict(BASE_COLORS)
        merged.update(self.theme.colors)
        return merged

    def layout_for(self, name: str | None = None) -> dict[str, Any]:
        """Per-screen layout tokens for ``name`` (or the active screen)."""
        return self.theme.layout_for(name or self.active_screen)

    def layout(self, key: str, default: Any = None, name: str | None = None) -> Any:
        """Return one layout token for the active screen, or ``default``."""
        return self.layout_for(name).get(key, default)

    @property
    def shadow_colors(self) -> tuple[int, int, int] | None:
        """Black shadow color when the theme requests text shadows, else None."""
        if not self.theme.text_shadow:
            return None
        return self.theme.colors.get("black", (0, 0, 0))

    def font(self, name: str) -> pygame.font.Font:
        try:
            return self.fonts[name]
        except KeyError:
            raise KeyError(
                f"No font named {name!r}. Available: {', '.join(sorted(self.fonts)) or '(none)'}"
            ) from None

    def asset(self, name: str) -> Any:
        try:
            return self.assets[name]
        except KeyError:
            raise KeyError(
                f"No asset named {name!r}. Available: {', '.join(sorted(self.assets)) or '(none)'}"
            ) from None

    def size(self) -> tuple[int, int]:
        if self.surface is None:
            return (0, 0)
        return self.surface.get_size()

    def width(self) -> int:
        return self.size()[0]

    def height(self) -> int:
        return self.size()[1]

    def clone(self, *, surface: pygame.Surface | None = None) -> AppContext:
        """Return a shallow copy bound to a (possibly new) surface."""
        return AppContext(
            surface=surface if surface is not None else self.surface,
            theme=self.theme,
            fonts=self.fonts,
            assets=self.assets,
            data=self.data,
            icon_manager=self.icon_manager,
            location=self.location,
            active_screen=self.active_screen,
        )

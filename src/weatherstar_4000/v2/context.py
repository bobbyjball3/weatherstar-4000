"""Runtime context shared by Screens and Components.

Replaces the legacy monolithic ``ws`` object.  The context carries the render
surface, resolved theme, named fonts/assets, and a :class:`DataRegistry` of
configured datasources so rendering code never reaches into a god object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

from weatherstar_4000.v2.themes import CLASSIC_THEME, ColorTheme


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
        theme: ColorTheme | None = None,
        fonts: dict[str, pygame.font.Font] | None = None,
        assets: dict[str, Any] | None = None,
        data: DataRegistry | None = None,
        icon_manager: Any = None,
        location: Location | None = None,
    ):
        self.surface = surface
        self.theme = theme or CLASSIC_THEME
        self.fonts: dict[str, pygame.font.Font] = fonts or {}
        self.assets: dict[str, Any] = assets or {}
        self.data = data or DataRegistry()
        self.icon_manager = icon_manager
        self.location = location

    # -- conveniences -------------------------------------------------------

    def get_color(self, key: str) -> tuple[int, int, int]:
        return self.theme.get_color(key)

    @property
    def colors(self) -> dict[str, tuple[int, int, int]]:
        """Theme colors merged over the authentic classic palette.

        Guarantees stable values for legacy keys (gray, orange, ...) that only
        exist in the classic theme while letting configured themes override.
        """
        merged = dict(CLASSIC_THEME.colors)
        merged.update(self.theme.colors)
        return merged

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
        )

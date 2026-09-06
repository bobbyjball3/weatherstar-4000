"""Icons media: registers an icon manager and a static icon dict.

The manager is self-contained (no legacy ``animated_icons`` dependency): it
preloads ``*.gif`` / ``*.png`` from the icons directory as plain surfaces and
serves scaled copies via ``get_icon(name, width, height)``.  GIFs render their
first frame; the manager is exposed through ``ctx.assets["icon_manager"]`` (and
thus ``ctx.icon_manager``) while ``ctx.assets["icons"]`` holds the raw surface
dict for simple blitting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

from weatherstar_4000.media.base import AssetMedia
from weatherstar_4000.registry import plugin


class IconManager:
    """Serves named weather-icon surfaces, optionally scaled."""

    def __init__(self, icons_dir: str | Path):
        self._icons = _load_icons(Path(icons_dir))

    def _find(self, name: str) -> pygame.Surface | None:
        if name in self._icons:
            return self._icons[name]
        lowered = name.lower()
        for key, surface in self._icons.items():
            if key.lower() == lowered:
                return surface
        return None

    def get_icon(
        self, name: str, width: int | None = None, height: int | None = None
    ) -> pygame.Surface | None:
        """Return the named icon surface, scaled to ``(width, height)`` when given."""
        surface = self._find(name)
        if surface is None:
            return None
        if width and height:
            try:
                return pygame.transform.scale(surface, (width, height))
            except pygame.error:  # pragma: no cover - degenerate size
                return surface
        return surface


def _lighten_glyph(surface: pygame.Surface) -> pygame.Surface:
    """Recolor near-black glyph art so icons read on dark graphics bands.

    The classic icon GIFs are black/colored line art on a white canvas that
    pygame loads with the white colorkeyed out.  Blitted over the app's dark
    navy bands that near-black line art is effectively invisible, so convert
    near-black glyph pixels to light while keeping genuine color fills (sun
    yellow, rain blue) and anti-aliased edges untouched.  Returns an RGBA
    surface whose colorkey (background) pixels are fully transparent.
    """
    key = surface.get_colorkey()
    key_rgb = key[:3] if key is not None else None
    out = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    surface.lock()
    out.lock()
    try:
        for y in range(surface.get_height()):
            for x in range(surface.get_width()):
                pixel = surface.get_at((x, y))
                rgb = (pixel[0], pixel[1], pixel[2])
                if key_rgb is not None and rgb == key_rgb:
                    continue  # transparent background
                if rgb[0] <= 70 and rgb[1] <= 70 and rgb[2] <= 70:
                    out.set_at((x, y), (255, 255, 255, 255))
                else:
                    out.set_at((x, y), (rgb[0], rgb[1], rgb[2], 255))
    finally:
        surface.unlock()
        out.unlock()
    return out


def _load_icons(directory: Path) -> dict[str, pygame.Surface]:
    result: dict[str, pygame.Surface] = {}
    if not directory.exists():
        return result
    for pattern in ("*.gif", "*.png"):
        for file_path in sorted(directory.glob(pattern)):
            if file_path.stem in result:
                continue
            try:
                surface = pygame.image.load(str(file_path))
                result[file_path.stem] = _lighten_glyph(surface)
            except pygame.error:  # pragma: no cover - corrupt asset
                continue
    return result


@plugin
class Icons(AssetMedia):
    name = "icons"
    asset_key = "icons"

    def load_asset(self, ctx: Any) -> dict[str, pygame.Surface]:
        directory = Path(self.asset_dir) / "icons"
        ctx.assets["icon_manager"] = IconManager(directory)
        return _load_icons(directory)

"""Fonts media: loads the Star4000 font set into ``ctx.fonts``.

Looked up from ``<asset_dir>/fonts_ttf`` when available, otherwise falls back to
named system monospace fonts, then to pygame's default font.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

from weatherstar_4000.v2.logging_setup import get_logger
from weatherstar_4000.v2.media import FontSet
from weatherstar_4000.v2.registry import plugin

log = get_logger("weatherstar4000.v2.fonts")

#: name -> (relative font file, size)
_FONT_SPECS = {
    "title": ("star4000.ttf", 32),
    "large": ("star4000_large.ttf", 32),
    "extended": ("star4000_extended.ttf", 32),
    "small": ("star4000_small.ttf", 28),
    "normal": ("star4000.ttf", 20),
    "forecast": ("star4000_small.ttf", 24),
    "tiny": ("star4000.ttf", 16),
    "scroller": ("star4000_extended.ttf", 24),
}

_FALLBACK_FONTS = ["consolas", "courier new", "courier", "monospace", "dejavu sans mono"]


def _fallback_font_path(bold: bool = False) -> str | None:
    for name in _FALLBACK_FONTS:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return path
    return None


@plugin
class Fonts(FontSet):
    name = "fonts"

    def load(self, ctx: Any) -> Any:
        fonts_dir = Path(self.asset_dir) / "fonts_ttf"
        if not fonts_dir.exists():  # pragma: no cover - depends on assets present
            fonts_dir = Path(self.asset_dir) / "fonts"
        loaded: dict[str, pygame.font.Font] = {}
        for key, (file_name, size) in _FONT_SPECS.items():
            font = self._load_one(fonts_dir, file_name, size)
            if font is not None:
                loaded[key] = font
        if not loaded:
            log.warning("no_star4000_fonts; falling back to system/default")
            for key, (_file_name, size) in _FONT_SPECS.items():
                loaded[key] = self._make_system_font(key, size)
        self.provide_fonts(ctx, loaded)
        return loaded

    @staticmethod
    def _load_one(fonts_dir: Path, file_name: str, size: int) -> pygame.font.Font | None:
        path = fonts_dir / file_name
        if path.exists():
            try:
                return pygame.font.Font(str(path), size)
            except pygame.error:  # pragma: no cover - corrupt font file
                log.warning("font_load_failed", path=str(path))
        return None

    @staticmethod
    def _make_system_font(key: str, size: int) -> pygame.font.Font:
        bold = key in {"title", "large", "extended", "scroller"}
        path = _fallback_font_path(bold=bold)
        if path:
            return pygame.font.Font(path, size)
        return pygame.font.Font(None, size)  # pragma: no cover - last resort

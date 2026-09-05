"""Backgrounds media: registers a dict of named background surfaces.

Surfaces are loaded from ``<asset_dir>/backgrounds/*.png`` keyed by file stem
(e.g. "1", "2", "BackGround1"); if none load, a default gradient surface is
generated and stored under the key "default".
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

from weatherstar_4000.media import AssetMedia
from weatherstar_4000.registry import plugin

_DEFAULT_SIZE = (640, 480)


def make_default_background(width: int, height: int) -> pygame.Surface:
    """Create a simple top-to-bottom blue gradient surface."""
    surface = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / height
        channel = int(128 + 127 * ratio)
        pygame.draw.line(surface, (0, 0, channel), (0, y), (width, y))
    return surface


@plugin
class Backgrounds(AssetMedia):
    name = "backgrounds"
    asset_key = "backgrounds"

    def load_asset(self, ctx: Any) -> dict[str, pygame.Surface]:
        directory = Path(self.asset_dir) / "backgrounds"
        result: dict[str, pygame.Surface] = {}
        if directory.exists():
            for file_path in sorted(directory.glob("*.png")):
                try:
                    result[file_path.stem] = pygame.image.load(str(file_path))
                except pygame.error:  # pragma: no cover - corrupt asset
                    continue
        if not result:
            width, height = ctx.size() or _DEFAULT_SIZE
            result["default"] = make_default_background(width, height)
        return result

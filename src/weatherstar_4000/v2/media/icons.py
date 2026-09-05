"""Icons media: registers an AnimatedIconManager and a static icon dict.

Reuses the already-tested ``weatherstar_4000.animated_icons`` module.  The
manager is exposed both through ``ctx.assets["icon_manager"]`` (used by the
engine to populate ``ctx.icon_manager``) and a plain dict of static icons under
``ctx.assets["icons"]`` for simple blitting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

from weatherstar_4000.animated_icons import AnimatedIconManager
from weatherstar_4000.v2.media import AssetMedia
from weatherstar_4000.v2.registry import plugin


@plugin
class Icons(AssetMedia):
    name = "icons"
    asset_key = "icons"

    def load_asset(self, ctx: Any) -> dict[str, pygame.Surface]:
        directory = Path(self.asset_dir) / "icons"
        manager = None
        try:
            manager = AnimatedIconManager(str(directory))
        except Exception:  # noqa: BLE001 - icons are best-effort decoration
            manager = None
        if manager is not None:
            ctx.assets["icon_manager"] = manager
        return _load_static_icons(directory)


def _load_static_icons(directory: Path) -> dict[str, pygame.Surface]:
    result: dict[str, pygame.Surface] = {}
    if directory.exists():
        for file_path in sorted(directory.glob("*.gif")):
            try:
                result[file_path.stem] = pygame.image.load(str(file_path))
            except pygame.error:  # pragma: no cover - corrupt asset
                continue
    return result

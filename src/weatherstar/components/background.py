"""Background component: fills the surface with a named background asset."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from pydantic import Field

from weatherstar.components.base import Component
from weatherstar.registry import plugin

if TYPE_CHECKING:
    from weatherstar.context import AppContext


@plugin
class Background(Component):
    """Fills the surface with a named background asset."""

    name = "background"

    background_name: str = Field(
        default="1", description="Background asset key to fill the screen (e.g. '1'..'6')."
    )

    def render(self, surface: pygame.Surface, ctx: AppContext) -> None:
        backgrounds = ctx.assets.get("backgrounds") or {}
        image = backgrounds.get(self.background_name)
        if image is None:
            image = next(iter(backgrounds.values()), None)
        if image is not None:
            surface.blit(image, (0, 0))
        else:
            surface.fill(ctx.colors["blue"])

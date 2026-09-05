"""Component abstraction: renderable units placed on a Screen.

Components are small, composable renderers (headers, text, icons, tables,
scrolling tickers, charts).  They receive the shared :class:`AppContext` and the
target surface at render time and read config through their own ConfigValue
descriptors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from weatherstar_4000.v2.plugin import Plugin

if TYPE_CHECKING:
    from weatherstar_4000.v2.context import AppContext


class Component(Plugin):
    """Base class for renderable components."""

    kind = "component"

    #: (x, y) position within the screen (0..1 normalised, or absolute px).
    position = (0, 0)

    def render(self, surface: pygame.Surface, ctx: AppContext) -> None:
        """Render this component onto ``surface`` using ``ctx``.

        Subclasses override.  ``surface`` is the screen or a sub-surface passed
        by the owning Screen.
        """
        raise NotImplementedError

    def prepare(self, ctx: AppContext) -> None:
        """Hook called once per engine run before the sequence starts."""

    def step(self, ctx: AppContext, dt: float) -> None:
        """Optional per-frame update hook for stateful/animated components."""

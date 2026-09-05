"""Screen abstraction: top-level container composed of Components + Media.

A Screen corresponds to one of the original WeatherStar displays.  It declares
which Component/Media/Datasource plugins it needs and draws them (plus any
screen-specific rendering) onto the shared surface for the duration of its
slide in the Sequence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pygame

from weatherstar_4000.plugin import Plugin

if TYPE_CHECKING:
    from weatherstar_4000.context import AppContext


class Screen(Plugin):
    """Base class for plugin screens."""

    kind = "screen"

    #: Ordered names of Component plugins to render before ``draw``.
    components: ClassVar[tuple[str, ...]] = ()
    #: Names of Datasource plugins this screen consumes.
    datasources: ClassVar[tuple[str, ...]] = ()
    #: Names of Media plugins this screen decorates itself with.
    media: ClassVar[tuple[str, ...]] = ()

    #: Optional per-slide background asset (e.g. "1") applied before draw.
    background: ClassVar[str | None] = None

    def draw(self, surface: pygame.Surface, ctx: AppContext, dt: float) -> None:
        """Render this screen onto ``surface`` for the current frame."""
        raise NotImplementedError

    def prepare(self, ctx: AppContext) -> None:
        """Optional hook called once before the sequence begins."""

    def step(self, ctx: AppContext, dt: float) -> None:
        """Optional per-frame update for animated screens."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{type(self).__name__} name={self.name!r}>"

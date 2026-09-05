"""Screen abstraction: top-level container composed of Components + Media.

A Screen corresponds to one of the original WeatherStar displays.  It declares
which Component/Media/Datasource plugins it needs and arranges an ordered
``layout`` of :class:`ComponentSpec`; the base :meth:`Screen.draw` renders those
components in order and then hands off to the :meth:`Screen.compose` hook for
any placement/animation that is not (yet) componentized.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

import pygame
from pydantic import PrivateAttr

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.plugin import Plugin
from weatherstar_4000.renderer import Renderer

if TYPE_CHECKING:
    from weatherstar_4000.context import AppContext


class Screen(Renderer, Plugin):
    """Base class for plugin screens."""

    kind = "screen"

    #: Ordered declarative layout of Component plugins rendered by ``draw``.
    layout: ClassVar[tuple[ComponentSpec, ...]] = ()
    #: Names of Datasource plugins this screen consumes.
    datasources: ClassVar[tuple[str, ...]] = ()
    #: Names of Media plugins this screen decorates itself with.
    media: ClassVar[tuple[str, ...]] = ()

    #: Component instances built by the engine from ``layout`` (runtime state).
    _components: list[Any] = PrivateAttr(default_factory=list)

    def draw(self, surface: pygame.Surface, ctx: AppContext, dt: float) -> None:
        """Step + render layout components, then hand off to ``compose``."""
        for component in self._components:
            component.step(ctx, dt)
            component.render(surface, ctx)
        self.compose(surface, ctx, dt)

    def compose(self, surface: pygame.Surface, ctx: AppContext, dt: float) -> None:
        """Hook for screen-specific drawing not covered by layout components.

        Subclasses override; the default draws nothing extra.
        """

    def bind_components(self, components: list[Any]) -> None:
        """Attach engine-built component instances (from ``layout``)."""
        self._components = list(components)

    def component(self, name: str) -> Any:
        """Return the first bound component plugin named ``name``."""
        for component in self._components:
            if component.name == name:
                return component
        raise KeyError(f"No component named {name!r} bound to {type(self).__name__}.")

    def prepare(self, ctx: AppContext) -> None:
        """Optional hook called once before the sequence begins."""

    def step(self, ctx: AppContext, dt: float) -> None:
        """Optional per-frame update for animated screens."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{type(self).__name__} name={self.name!r}>"

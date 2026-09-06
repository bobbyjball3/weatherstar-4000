"""Screen abstraction: top-level container composed of Components + Media.

A Screen corresponds to one of the original WeatherStar displays.  It declares
which Component/Media/Datasource plugins it needs and arranges an ordered
``layout`` of :class:`ComponentSpec`; the base :meth:`Screen.draw` renders those
components in order and then hands off to the screen's ``compose_<variant>``
renderers.

Theming contract
----------------
A screen declares which layout families (:class:`LayoutVariant`) it renders and
the method that draws each via the ``variants`` ClassVar::

    class CurrentConditionsScreen(Screen):
        variants = {
            LayoutVariant.WS4000: "compose_4000",
            LayoutVariant.WS3000: "compose_3000",
        }

        def compose_4000(self, surface, ctx, dt): ...
        def compose_3000(self, surface, ctx, dt): ...

The base :meth:`Screen.compose` resolves the active theme's variant (see
:meth:`Renderer.variant`) and dispatches to the mapped method.  When the active
theme requests a variant the screen has not declared, it raises
:class:`ThemeNotSupported` so the engine can degrade gracefully (a centered
placeholder at runtime, a per-slide failure under ``--validate``).

A screen that draws only through its ``layout`` components declares nothing and
inherits an empty ``variants`` map - ``compose`` then draws nothing extra.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

import pygame
from pydantic import PrivateAttr

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.errors import ThemeNotSupported
from weatherstar_4000.plugin import Plugin
from weatherstar_4000.renderer import Renderer
from weatherstar_4000.themes import LayoutVariant

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
    #: Layout variant -> renderer method name.  Screens that render entirely
    #: through ``layout`` components leave this empty (inherited default).
    variants: ClassVar[dict[LayoutVariant, str]] = {}

    #: Component instances built by the engine from ``layout`` (runtime state).
    _components: list[Any] = PrivateAttr(default_factory=list)

    def draw(self, surface: pygame.Surface, ctx: AppContext, dt: float) -> None:
        """Step + render layout components, then hand off to ``compose``."""
        for component in self._components:
            component.step(ctx, dt)
            component.render(surface, ctx)
        self.compose(surface, ctx, dt)

    def compose(self, surface: pygame.Surface, ctx: AppContext, dt: float) -> None:
        """Dispatch to the ``compose_<variant>`` method the active theme requests.

        The variant comes from the theme (per-screen ``variant`` layout token,
        else ``Theme.variant``).  When no method is mapped for it the screen
        raises :class:`ThemeNotSupported`; component-only screens (empty
        ``variants``) draw nothing extra here.
        """
        variant = self.variant(ctx)
        method_name = type(self).variants.get(variant)
        if method_name is not None:
            getattr(self, method_name)(surface, ctx, dt)
            return
        if type(self).variants:
            screen_name = getattr(self, "name", None) or type(self).__name__
            raise ThemeNotSupported(screen_name, variant, tuple(type(self).variants))

    @classmethod
    def supported_variants(cls) -> tuple[LayoutVariant, ...]:
        """The layout variants this screen declares, sorted by value."""
        return tuple(sorted(cls.variants, key=lambda item: item.value))

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

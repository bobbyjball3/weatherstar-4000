"""Media abstraction: local media sources attachable to Screens/Components.

Fonts, images, animated GIFs, logos and music are all Media plugins.  A Media's
:meth:`load` is called by the engine to populate the shared :class:`AppContext`
(fonts dict, asset registry, icon manager, music player), after which Screens
and Components can reference the loaded resource by name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from weatherstar_4000.v2.config import ConfigValue
from weatherstar_4000.v2.plugin import Plugin

if TYPE_CHECKING:
    from weatherstar_4000.v2.context import AppContext


class Media(Plugin):
    """Base class for local media plugins."""

    kind = "media"

    asset_dir = ConfigValue(default="static_assets", type=str)

    def load(self, ctx: AppContext) -> Any:
        """Load this media into ``ctx`` (fonts/assets) and return the resource.

        Implementations should be idempotent: the engine may load a media plugin
        once per run.
        """
        raise NotImplementedError


class FontSet(Media):
    """Named collection of pygame fonts, registered into ``ctx.fonts``.

    Concrete font-set plugins set ``name`` and override ``load`` to call
    :meth:`provide_fonts`.
    """

    def provide_fonts(self, ctx: AppContext, fonts: dict[str, Any]) -> None:
        ctx.fonts.update(fonts)


class AssetMedia(Media):
    """Base for media that register a single named asset into ``ctx.assets``.

    Concrete plugins set a plain ``asset_key`` class attribute and implement
    :meth:`load_asset`.
    """

    #: Plain attribute (not a ConfigValue) naming the ctx.assets entry.
    asset_key: str | None = None

    def load_asset(self, ctx: AppContext) -> Any:
        raise NotImplementedError

    def load(self, ctx: AppContext) -> Any:
        resource = self.load_asset(ctx)
        key = self.asset_key or self.name
        if resource is not None:
            ctx.assets[key] = resource
        return resource

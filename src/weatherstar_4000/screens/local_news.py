"""Local News screen: city header plus live local headlines.

Headlines come from the ``local_news`` datasource (real Google News when
available, bundled simulated headlines otherwise).  The ``headlines`` component
scrolls them and shows a friendly placeholder when the feed is empty.
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen


@plugin
class LocalNewsScreen(Screen):
    name = "local_news"
    media = ("backgrounds", "logos")
    datasources = ("local_news", "weather")
    layout = (
        ComponentSpec(component="background", config={"background_name": "1"}),
        ComponentSpec(component="header", config={"title_top": "Local News", "title_bottom": ""}),
        ComponentSpec(component="clock"),
        ComponentSpec(
            component="headlines",
            config={
                "numbered": True,
                "accent": "category",
                "red_terms": ("BREAKING", "EMERGENCY", "ALERT"),
                "yellow_terms": (),
                "datasource_name": "local_news",
                "empty_text": "No local headlines are available right now",
            },
        ),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        city_text = self.text_surface(ctx, self._resolve_city(ctx).upper(), color_key="yellow")
        surface.blit(city_text, city_text.get_rect(centerx=320, y=65))

    def _resolve_city(self, ctx: Any) -> str:
        lat, lon = self.latlon(ctx)
        news = self.datasource(ctx, "local_news")
        if news is not None and callable(getattr(news, "city_name", None)):
            try:
                name = news.city_name(lat, lon)
                if name:
                    return str(name)
            except Exception:  # noqa: BLE001 - fall through to weather/location
                pass
        weather = self.datasource(ctx, "weather")
        if weather is not None and callable(getattr(weather, "get_city", None)):
            try:
                city, _state = weather.get_city(lat, lon)
                if city:
                    return str(city)
            except Exception:  # noqa: BLE001 - fall through to location
                pass
        location = getattr(ctx, "location", None)
        if location is not None and getattr(location, "description", ""):
            return str(location.description)
        return "Local Area"

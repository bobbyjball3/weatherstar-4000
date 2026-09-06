"""Travel Cities screen: static grid of major US city weather."""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen
from weatherstar_4000.themes import LayoutVariant


@plugin
class TravelCitiesScreen(Screen):
    name = "travel_cities"
    media = ("fonts", "backgrounds", "logos", "icons")
    datasources = ()

    variants = {
        LayoutVariant.WS4000: "compose_4000",
    }

    layout = (
        ComponentSpec(component="background", config={"background_name": "5"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Travel Cities", "title_bottom": "Weather", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose_4000(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        cities = [
            ("NEW YORK", 72, "Partly Cloudy"),
            ("LOS ANGELES", 78, "Sunny"),
            ("CHICAGO", 65, "Cloudy"),
            ("MIAMI", 85, "T-Storms"),
            ("DALLAS", 88, "Mostly Sunny"),
            ("SEATTLE", 62, "Rain"),
            ("DENVER", 70, "Clear"),
            ("ATLANTA", 79, "Partly Cloudy"),
        ]

        yellow = self.color(ctx, "yellow")
        white = self.color(ctx, "white")
        y_pos = 120

        for i, (city, temp, conditions) in enumerate(cities):
            if i % 2 == 1:
                bar_rect = pygame.Rect(60, y_pos - 5, 520, 30)
                pygame.draw.rect(surface, (0, 0, 60), bar_rect)

            city_surf = self.font(ctx, "normal").render(city, True, yellow)
            surface.blit(city_surf, (80, y_pos))

            temp_surf = self.font(ctx, "normal").render(f"{temp}\N{DEGREE SIGN}", True, white)
            surface.blit(temp_surf, (320, y_pos))

            cond_surf = self.font(ctx, "normal").render(conditions, True, white)
            surface.blit(cond_surf, (400, y_pos))

            y_pos += 35

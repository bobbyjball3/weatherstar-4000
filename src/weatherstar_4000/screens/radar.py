"""Radar screen: animated NOAA radar cropped around the configured location.

Uses the ``radar`` datasource, which returns regional (location-zoomed) frames
scaled to the radar box.  Frames cycle every ~0.5s like the legacy display.
When no frames are available (offline/startup) a "RADAR UPDATING" placeholder is
shown, and the datasource retries on its own TTL.
"""

from __future__ import annotations

from typing import Any

import pygame
from pydantic import PrivateAttr

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen

_RADAR_RECT = pygame.Rect(70, 100, 500, 300)
_FRAME_DURATION = 0.5  # seconds per radar frame

_LEGEND = (
    ((0, 100, 0), "Light"),
    ((255, 255, 0), "Moderate"),
    ((255, 140, 0), "Heavy"),
    ((255, 0, 0), "Intense"),
)


@plugin
class RadarScreen(Screen):
    name = "radar"
    media = ("fonts", "backgrounds", "logos")
    datasources = ("radar",)

    _frames: list[pygame.Surface] = PrivateAttr(default_factory=list)
    _frame_index: int = PrivateAttr(default=0)
    _frame_timer: float = PrivateAttr(default=0.0)

    def _radar_frames(self, ctx: Any) -> list[pygame.Surface]:
        location = getattr(ctx, "location", None)
        if location is None:
            return []
        try:
            radar = self.datasource(ctx, "radar")
            return radar.frames(location.lat, location.lon) or []
        except Exception:
            return []

    layout = (
        ComponentSpec(component="background", config={"background_name": "6"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Live", "title_bottom": "Radar", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
    )

    def compose(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        rect = _RADAR_RECT
        white = self.color(ctx, "white", (255, 255, 255))
        yellow = self.color(ctx, "yellow", (255, 255, 0))

        frames = self._frames or self._radar_frames(ctx)
        self._frames = frames

        if frames:
            self._frame_timer += dt
            if self._frame_timer >= _FRAME_DURATION:
                self._frame_timer = 0.0
                self._frame_index = (self._frame_index + 1) % len(frames)
            surface.blit(frames[self._frame_index], rect)
            self._draw_legend(surface, ctx, rect)
            frame_text = self.font(ctx, "tiny").render(
                f"Frame {self._frame_index + 1}/{len(frames)}", True, white
            )
            surface.blit(frame_text, (rect.right - 100, rect.bottom - 20))
        else:
            pygame.draw.rect(surface, (0, 20, 40), rect)
            msg = self.font(ctx, "large").render("RADAR UPDATING", True, yellow)
            surface.blit(msg, msg.get_rect(center=rect.center))
            msg2 = self.font(ctx, "normal").render("Connecting to NOAA Radar...", True, white)
            surface.blit(msg2, msg2.get_rect(center=(rect.centerx, rect.centery + 30)))

        pygame.draw.rect(surface, yellow, rect, 2)

        location = self._location_text(ctx)
        loc_font = self.font(ctx, "normal")
        loc_text = loc_font.render(location.upper(), True, yellow)
        surface.blit(loc_text, loc_text.get_rect(center=(320, 420)))

        attr = self.font(ctx, "tiny").render("Radar: NOAA/NWS", True, white)
        surface.blit(attr, (rect.left, rect.bottom + 5))

    def _draw_legend(self, surface: pygame.Surface, ctx: Any, rect: pygame.Rect) -> None:
        legend_y = rect.top + 10
        legend_x = rect.left + 10
        white = self.color(ctx, "white", (255, 255, 255))
        tiny = self.font(ctx, "tiny")
        for i, (color, label) in enumerate(_LEGEND):
            box = pygame.Rect(legend_x, legend_y + i * 20, 15, 15)
            pygame.draw.rect(surface, color, box)
            pygame.draw.rect(surface, white, box, 1)
            text = tiny.render(label, True, white)
            surface.blit(text, (legend_x + 20, legend_y + i * 20))

    def _location_text(self, ctx: Any) -> str:
        location = getattr(ctx, "location", None)
        if location is None:
            return ""
        description = getattr(location, "description", "") or ""
        if description:
            return description
        weather = self.optional_datasource(ctx, "weather")
        if weather is not None:
            try:
                city = weather.get_city(location.lat, location.lon)
                if city.city and city.state:
                    return f"{city.city}, {city.state}"
            except Exception:
                pass
        return ""

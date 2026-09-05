"""Radar screen: animated NOAA radar cropped around the configured location.

Uses the ``radar`` datasource, which returns regional (location-zoomed) frames
scaled to the radar box.  Frames cycle every ~0.5s like the legacy display.
When no frames are available (offline/startup) a "RADAR UPDATING" placeholder is
shown, and the datasource retries on its own TTL.
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

_RADAR_RECT = pygame.Rect(70, 100, 500, 300)
_FRAME_DURATION = 0.5  # seconds per radar frame

_LEGEND = (
    ((0, 100, 0), "Light"),
    ((255, 255, 0), "Moderate"),
    ((255, 140, 0), "Heavy"),
    ((255, 0, 0), "Intense"),
)


def _font(ctx: Any, name: str, size: int) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None) or {}
    return fonts.get(name) or pygame.font.Font(None, size)


def _color(ctx: Any, key: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
    colors = getattr(ctx, "colors", None) or {}
    return colors.get(key, default)


@plugin
class RadarScreen(Screen):
    name = "radar"
    media = ("fonts", "backgrounds", "logos")
    datasources = ("radar",)

    def prepare(self, ctx: Any) -> None:
        self._frames: list[pygame.Surface] = []
        self._frame_index = 0
        self._frame_timer = 0.0

    def _radar_frames(self, ctx: Any) -> list[pygame.Surface]:
        location = getattr(ctx, "location", None)
        if location is None:
            return []
        try:
            radar = ctx.data.get("radar")
            return radar.frames(location.lat, location.lon) or []
        except Exception:
            return []

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "6")
        render.draw_header(surface, ctx, "Live", "Radar")

        rect = _RADAR_RECT
        white = _color(ctx, "white", (255, 255, 255))
        yellow = _color(ctx, "yellow", (255, 255, 0))

        frames = self._frames or self._radar_frames(ctx)
        self._frames = frames

        if frames:
            self._frame_timer += dt
            if self._frame_timer >= _FRAME_DURATION:
                self._frame_timer = 0.0
                self._frame_index = (self._frame_index + 1) % len(frames)
            surface.blit(frames[self._frame_index], rect)
            self._draw_legend(surface, ctx, rect)
            frame_text = _font(ctx, "tiny", 16).render(
                f"Frame {self._frame_index + 1}/{len(frames)}", True, white
            )
            surface.blit(frame_text, (rect.right - 100, rect.bottom - 20))
        else:
            pygame.draw.rect(surface, (0, 20, 40), rect)
            msg = _font(ctx, "large", 32).render("RADAR UPDATING", True, yellow)
            surface.blit(msg, msg.get_rect(center=rect.center))
            msg2 = _font(ctx, "normal", 20).render("Connecting to NOAA Radar...", True, white)
            surface.blit(msg2, msg2.get_rect(center=(rect.centerx, rect.centery + 30)))

        pygame.draw.rect(surface, yellow, rect, 2)

        location = self._location_text(ctx)
        loc_font = _font(ctx, "normal", 20)
        loc_text = loc_font.render(location.upper(), True, yellow)
        surface.blit(loc_text, loc_text.get_rect(center=(320, 420)))

        attr = _font(ctx, "tiny", 16).render("Radar: NOAA/NWS", True, white)
        surface.blit(attr, (rect.left, rect.bottom + 5))

    def _draw_legend(self, surface: pygame.Surface, ctx: Any, rect: pygame.Rect) -> None:
        legend_y = rect.top + 10
        legend_x = rect.left + 10
        white = _color(ctx, "white", (255, 255, 255))
        tiny = _font(ctx, "tiny", 16)
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
        weather = None
        try:
            weather = ctx.data.get("weather")
        except Exception:
            pass
        if weather is not None:
            try:
                city, state = weather.get_city(location.lat, location.lon)
                if city and state:
                    return f"{city}, {state}"
            except Exception:
                pass
        return ""

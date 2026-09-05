"""Local News screen: city header plus live local headlines.

Headlines come from the ``local_news`` datasource (real Google News when
available, bundled simulated headlines otherwise).  When empty, a friendly
placeholder is shown instead of a blank box.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame
from pydantic import PrivateAttr

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

_CLIP_RECT = pygame.Rect(55, 100, 530, 298)
_LINE_HEIGHT = 28
_HEADLINE_SPACING = 15
_WRAP_WIDTH = 470
_SCROLL_SPEED = 20.0

_EMERGENCY_WORDS = ("EMERGENCY", "BREAKING", "ALERT")


def _font(ctx: Any, name: str, size: int) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None) or {}
    return fonts.get(name) or pygame.font.Font(None, size)


def _color(ctx: Any, key: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
    colors = getattr(ctx, "colors", None) or {}
    return colors.get(key, default)


def _ds(ctx: Any, name: str) -> Any:
    data = getattr(ctx, "data", None)
    if data is None:
        return None
    try:
        return data.get(name)
    except Exception:  # noqa: BLE001 - optional datasource
        return None


def _latlon(ctx: Any) -> tuple[float, float]:
    location = getattr(ctx, "location", None)
    if location is None:
        return 0.0, 0.0
    return float(getattr(location, "lat", 0.0)), float(getattr(location, "lon", 0.0))


@plugin
class LocalNewsScreen(Screen):
    name = "local_news"
    media = ("backgrounds", "fonts", "logos")
    datasources = ("local_news", "weather")
    _scroll: float = PrivateAttr(default=200.0)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "1")
        render.draw_header(surface, ctx, "Local News")

        city_name = self._resolve_city(ctx).upper()
        city_font = _font(ctx, "normal", 20)
        city_text = city_font.render(city_name, True, _color(ctx, "yellow", (255, 255, 0)))
        city_rect = city_text.get_rect(centerx=320, y=65)
        surface.blit(city_text, city_rect)

        lat, lon = _latlon(ctx)
        headlines: list[tuple[str, str]] = []
        ds = _ds(ctx, "local_news")
        if ds is not None:
            try:
                headlines = list(ds.headlines(lat, lon) or [])
            except Exception:  # noqa: BLE001 - data is optional
                headlines = []

        if not headlines:
            message = _font(ctx, "normal", 20).render(
                "No local headlines are available right now",
                True,
                _color(ctx, "white", (255, 255, 255)),
            )
            surface.blit(message, message.get_rect(center=(320, 240)))
            return

        self._draw_headlines(surface, ctx, headlines, dt)

    def _resolve_city(self, ctx: Any) -> str:
        lat, lon = _latlon(ctx)
        ds = _ds(ctx, "local_news")
        if ds is not None:
            try:
                name = ds.city_name(lat, lon)
                if name:
                    return str(name)
            except Exception:  # noqa: BLE001 - fall through
                pass
        weather = _ds(ctx, "weather")
        if weather is not None:
            try:
                city, _state = weather.get_city(lat, lon)
                if city:
                    return str(city)
            except Exception:  # noqa: BLE001 - fall through
                pass
        location = getattr(ctx, "location", None)
        if location is not None and getattr(location, "description", ""):
            return str(location.description)
        return "Local Area"

    def _draw_headlines(
        self,
        surface: pygame.Surface,
        ctx: Any,
        headlines: list[tuple[str, str]],
        dt: float,
    ) -> None:
        news_font = _font(ctx, "small", 20)
        num_font = _font(ctx, "normal", 22)
        yellow = _color(ctx, "yellow", (255, 255, 0))

        scroll = float(getattr(self, "_scroll", 200.0))
        surface.set_clip(_CLIP_RECT)
        y_pos = scroll

        for i, headline in enumerate(headlines, 1):
            text = headline[0] if isinstance(headline, (tuple, list)) else headline
            lines = self._wrap(news_font, text)

            if -200 < y_pos < 500:
                number = num_font.render(f"{i}.", True, yellow)
                surface.blit(number, (65, y_pos))

                line_y = y_pos
                for line in lines:
                    if 95 < line_y < 398:
                        self._draw_line(surface, ctx, news_font, line, 95, line_y)
                    line_y += _LINE_HEIGHT
                y_pos = line_y + _HEADLINE_SPACING
            else:
                y_pos += _LINE_HEIGHT * 2 + _HEADLINE_SPACING

        surface.set_clip(None)

        dt = dt or 0.0
        scroll -= dt * _SCROLL_SPEED
        if y_pos < 100:
            scroll = 440.0
        self._scroll = scroll

        update_time = datetime.now().strftime("%I:%M %p")
        footer = news_font.render(f"Updated: {update_time}", True, yellow)
        surface.blit(footer, footer.get_rect(center=(320, 440)))

    def _wrap(self, font: pygame.font.Font, text: str) -> list[str]:
        lines: list[str] = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip() if current else word
            if font.size(candidate)[0] > _WRAP_WIDTH and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def _draw_line(
        self,
        surface: pygame.Surface,
        ctx: Any,
        font: pygame.font.Font,
        line: str,
        x: int,
        y: int,
    ) -> None:
        white = _color(ctx, "white", (255, 255, 255))
        if ":" not in line:
            surface.blit(font.render(line, True, white), (x, y))
            return

        category, rest = line.split(":", 1)
        if any(word in category.upper() for word in _EMERGENCY_WORDS):
            color = _color(ctx, "red", (255, 0, 0))
        else:
            color = _color(ctx, "cyan", (0, 255, 255))

        category_text = font.render(f"{category}:", True, color)
        rest_text = font.render(rest, True, white)
        surface.blit(category_text, (x, y))
        surface.blit(rest_text, (x + category_text.get_width(), y))

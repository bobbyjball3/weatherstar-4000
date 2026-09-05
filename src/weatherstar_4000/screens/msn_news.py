"""MSN Top Stories screen with a vertical headline ticker.

Headlines are a module-level literal (as in the legacy display source) and are
drawn with the classic color coding: category prefixes in cyan, ``BREAKING`` in
red and ``UPDATE`` in yellow.  Scrolling is time based, accumulating ``dt`` on
the instance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame
from pydantic import PrivateAttr

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

#: Literal headline set ported from ``displays.py::draw_msn_news``.
MSN_HEADLINES: list[tuple[str, str]] = [
    (
        "Breaking: Major Winter Storm System Moving Across United States "
        "Bringing Heavy Snow and Ice",
        "https://www.msn.com/weather",
    ),
    (
        "Technology: Apple Announces Revolutionary New Product Line at Annual Developer Conference",
        "https://www.msn.com/technology",
    ),
    (
        "Sports: Underdog Team Wins Championship in Dramatic Overtime Victory Against All Odds",
        "https://www.msn.com/sports",
    ),
    (
        "World News: Global Climate Summit Concludes with Historic Agreement Among Nations",
        "https://www.msn.com/world",
    ),
    (
        "Business: Stock Market Reaches All-Time High as Economic Recovery Continues to Accelerate",
        "https://www.msn.com/money",
    ),
    (
        "Entertainment: Surprise Winners at Annual Award Show Leave Audiences Stunned",
        "https://www.msn.com/entertainment",
    ),
    (
        "Health: Scientists Announce Major Medical Breakthrough in Cancer Research Treatment",
        "https://www.msn.com/health",
    ),
    (
        "Science: Space Mission Successfully Launches New Era of Deep Space Exploration",
        "https://www.msn.com/news/technology",
    ),
    (
        "Politics: Congress Passes Landmark Legislation with Bipartisan Support",
        "https://www.msn.com/politics",
    ),
    (
        "Local: Community Rallies Together to Support Families Affected by Recent Events",
        "https://www.msn.com/local",
    ),
    (
        "Weather: Hurricane Season Expected to Be More Active Than Normal This Year",
        "https://www.weather.com",
    ),
    (
        "Technology: Artificial Intelligence Breakthrough Could Transform Daily Life",
        "https://www.msn.com/technology",
    ),
]

_CLIP_RECT = pygame.Rect(55, 100, 530, 298)
_LINE_HEIGHT = 28
_HEADLINE_SPACING = 15
_WRAP_WIDTH = 470
_SCROLL_SPEED = 20.0


def _font(ctx: Any, name: str, size: int) -> pygame.font.Font:
    fonts = getattr(ctx, "fonts", None) or {}
    return fonts.get(name) or pygame.font.Font(None, size)


def _color(ctx: Any, key: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
    colors = getattr(ctx, "colors", None) or {}
    return colors.get(key, default)


@plugin
class MsnNewsScreen(Screen):
    name = "msn_news"
    media = ("backgrounds", "fonts", "logos")
    _scroll: float = PrivateAttr(default=200.0)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "1")
        render.draw_header(surface, ctx, "MSN", "Top Stories")

        if not MSN_HEADLINES:
            message = _font(ctx, "normal", 20).render(
                "No headlines available", True, _color(ctx, "white", (255, 255, 255))
            )
            surface.blit(message, message.get_rect(center=(320, 240)))
            return

        self._draw_headlines(surface, ctx, MSN_HEADLINES, dt)

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
        upper = category.upper()
        if upper == "BREAKING":
            color = _color(ctx, "red", (255, 0, 0))
        elif upper == "UPDATE":
            color = _color(ctx, "yellow", (255, 255, 0))
        else:
            color = _color(ctx, "cyan", (0, 255, 255))

        category_text = font.render(f"{category}:", True, color)
        rest_text = font.render(rest, True, white)
        surface.blit(category_text, (x, y))
        surface.blit(rest_text, (x + category_text.get_width(), y))

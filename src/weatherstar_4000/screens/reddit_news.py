"""Reddit Headlines screen with a vertical headline ticker.

Headlines are a module-level literal (as in the legacy display source).  Each
line is drawn token by token so ``r/...`` subreddit mentions render in cyan and
bracketed tags (``[OC]``) in yellow.  Scrolling accumulates ``dt`` on the
instance and wraps when the list has scrolled past the top.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pygame
from pydantic import PrivateAttr

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

#: Literal headline set ported from ``displays.py::draw_reddit_news``.
REDDIT_HEADLINES: list[tuple[str, str]] = [
    (
        "r/news: Major Storm System Approaching East Coast with Potential for "
        "Historic Snowfall Amounts",
        "https://reddit.com/r/news",
    ),
    (
        "r/worldnews: International Summit Concludes with Unexpected Alliance "
        "Between Former Rivals",
        "https://reddit.com/r/worldnews",
    ),
    (
        "r/technology: New AI Breakthrough Could Revolutionize How We Interact with Computers",
        "https://reddit.com/r/technology",
    ),
    (
        "r/science: Scientists Discover New Species in Previously Unexplored Deep Ocean Trench",
        "https://reddit.com/r/science",
    ),
    (
        "r/gaming: Popular Game Franchise Gets Surprise Major Update After Years of Silence",
        "https://reddit.com/r/gaming",
    ),
    (
        "r/movies: Independent Film Breaks Box Office Records in Limited Release",
        "https://reddit.com/r/movies",
    ),
    (
        "r/sports: Underdog Team's Cinderella Story Continues with Another Upset Victory",
        "https://reddit.com/r/sports",
    ),
    (
        "r/space: New Images from James Webb Space Telescope Reveal Stunning Cosmic Phenomena",
        "https://reddit.com/r/space",
    ),
    (
        "r/AskReddit: What's the most interesting historical fact you know that sounds fake?",
        "https://reddit.com/r/AskReddit",
    ),
    (
        "r/todayilearned: TIL that honey never spoils and archaeologists have "
        "found 3000 year old honey",
        "https://reddit.com/r/todayilearned",
    ),
    (
        "r/EarthPorn: Sunrise over the Grand Canyon after fresh snowfall [OC] [4032x3024]",
        "https://reddit.com/r/EarthPorn",
    ),
    (
        "r/dataisbeautiful: [OC] Visualization of global temperature changes over the last century",
        "https://reddit.com/r/dataisbeautiful",
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
class RedditNewsScreen(Screen):
    name = "reddit_news"
    media = ("backgrounds", "fonts", "logos")
    _scroll: float = PrivateAttr(default=200.0)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "1")
        render.draw_header(surface, ctx, "Reddit", "Headlines")

        if not REDDIT_HEADLINES:
            message = _font(ctx, "normal", 20).render(
                "No headlines available", True, _color(ctx, "white", (255, 255, 255))
            )
            surface.blit(message, message.get_rect(center=(320, 240)))
            return

        self._draw_headlines(surface, ctx, REDDIT_HEADLINES, dt)

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
        cyan = _color(ctx, "cyan", (0, 255, 255))
        yellow = _color(ctx, "yellow", (255, 255, 0))

        x_pos = x
        for part in line.split():
            if part.startswith("r/") or part.startswith("/r/"):
                color = cyan
            elif part.startswith("[") and part.endswith("]"):
                color = yellow
            else:
                color = white
            text = font.render(part, True, color)
            surface.blit(text, (x_pos, y))
            x_pos += text.get_width() + 5

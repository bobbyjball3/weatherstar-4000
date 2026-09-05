"""Shared drawing helpers used by Screens/Components.

These reproduce the classic WeatherStar header/background look so ported screens
stay visually faithful while reading everything from the AppContext instead of a
god object.
"""

from __future__ import annotations

from datetime import datetime

import pygame

from weatherstar_4000.v2.context import AppContext


def draw_background(surface: pygame.Surface, ctx: AppContext, name: str = "1") -> None:
    """Blit a named background, falling back to the first available."""
    backgrounds = ctx.assets.get("backgrounds")
    if not backgrounds:
        surface.fill(ctx.colors["blue"])
        return
    image = backgrounds.get(name)
    if image is None:
        first = next(iter(backgrounds.values()), None)
        image = first
    if image is not None:
        surface.blit(image, (0, 0))


def draw_header(
    surface: pygame.Surface,
    ctx: AppContext,
    title_top: str,
    title_bottom: str | None = None,
    has_noaa: bool = False,
) -> None:
    """Draw the standard header: corner logo, yellow title, NOAA mark, clock/date."""
    logos = ctx.assets.get("logos") or {}
    colors = ctx.colors
    fonts = ctx.fonts

    if "logo-corner" in logos:
        surface.blit(logos["logo-corner"], (50, 25))

    title_font = fonts.get("title", fonts.get("large"))
    if title_bottom:
        text1 = title_font.render(title_top.upper(), True, colors["yellow"])
        text2 = title_font.render(title_bottom.upper(), True, colors["yellow"])
        surface.blit(text1, (170, 27))
        surface.blit(text2, (170, 53))
    else:
        text = title_font.render(title_top.upper(), True, colors["yellow"])
        surface.blit(text, (170, 40))

    if has_noaa and "noaa" in logos:
        surface.blit(logos["noaa"], (356, 39))

    small = fonts.get("small", title_font)
    time_str = datetime.now().strftime("%I:%M %p").lstrip("0")
    time_text = small.render(time_str, True, colors["white"])
    time_rect = time_text.get_rect(right=590, y=34)
    surface.blit(time_text, time_rect)

    date_str = datetime.now().strftime("%a %b %d").upper()
    date_text = small.render(date_str, True, colors["white"])
    date_rect = date_text.get_rect(right=590, y=54)
    surface.blit(date_text, date_rect)


def draw_centered_text(
    surface: pygame.Surface,
    ctx: AppContext,
    text: str,
    y: int,
    font_name: str = "small",
    color_key: str = "white",
    center_x: int | None = None,
) -> pygame.Rect:
    font = ctx.fonts.get(font_name, pygame.font.Font(None, 20))
    rendered = font.render(text, True, ctx.colors[color_key])
    width = surface.get_width() if center_x is None else 2 * center_x
    rect = rendered.get_rect(center=(width // 2, y))
    surface.blit(rendered, rect)
    return rect


def draw_text(
    surface: pygame.Surface,
    ctx: AppContext,
    text: str,
    pos: tuple[int, int],
    font_name: str = "small",
    color_key: str = "white",
) -> pygame.Rect:
    font = ctx.fonts.get(font_name, pygame.font.Font(None, 20))
    rendered = font.render(text, True, ctx.colors[color_key])
    surface.blit(rendered, pos)
    return rendered.get_rect(topleft=pos)

"""Air Quality & Health screen (port of legacy ``draw_air_quality``).

Content is static in the legacy simulator: a fixed AQI value (45 / GOOD), a
small AQI scale reference, color-coded pollen bars, and health recommendations
with a small vertical scroll animation.
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000.v2 import render
from weatherstar_4000.v2.registry import plugin
from weatherstar_4000.v2.screen import Screen

_GREEN = (0, 255, 0)
_SOFT_GREEN = (100, 255, 100)
_ORANGE = (255, 165, 0)
_SOFT_RED = (255, 100, 100)
_YELLOW = (255, 255, 0)
_WHITE = (255, 255, 255)

_MAX_TIP_WIDTH = 500


def _font(ctx: Any, key: str) -> pygame.font.Font | None:
    """Return a named font, falling back to the first available font."""
    font = ctx.fonts.get(key)
    if font is None and ctx.fonts:
        font = next(iter(ctx.fonts.values()))
    return font


def _blit(surface: pygame.Surface, ctx: Any, font_key: str, text: str, pos, color) -> None:
    font = _font(ctx, font_key)
    if font is None:
        return
    surface.blit(font.render(text, True, color), pos)


def _wrap(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    """Word-wrap ``text`` so no line exceeds ``max_width`` pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


@plugin
class AirQualityScreen(Screen):
    name = "air_quality"
    media = ("backgrounds",)
    datasources = ()

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "5")
        render.draw_header(surface, ctx, "Air Quality", "& Health")

        colors = ctx.colors
        yellow = colors.get("yellow", _YELLOW)
        white = colors.get("white", _WHITE)

        left_x = 80
        right_x = 350
        y_pos = 120

        _blit(surface, ctx, "normal", "AIR QUALITY INDEX", (left_x, y_pos), yellow)
        y_pos += 30

        aqi_value = 45
        aqi_text = "GOOD"

        pygame.draw.rect(surface, _GREEN, (left_x, y_pos, 60, 40), 2)
        font_normal = _font(ctx, "normal")
        if font_normal is not None:
            num = font_normal.render(str(aqi_value), True, _GREEN)
            surface.blit(num, num.get_rect(center=(left_x + 30, y_pos + 20)))
        font_small = _font(ctx, "small")
        if font_small is not None:
            desc = font_small.render(aqi_text, True, _GREEN)
            surface.blit(desc, (left_x + 70, y_pos + 12))
        y_pos += 50

        scale = [
            ("0-50", "Good", _GREEN),
            ("51-100", "Moderate", yellow),
            ("101-150", "Sensitive Groups", _ORANGE),
        ]
        for range_txt, desc, color in scale:
            _blit(surface, ctx, "small", f"{range_txt}: {desc}", (left_x, y_pos), color)
            y_pos += 22

        pollen_y = 120
        _blit(surface, ctx, "normal", "POLLEN COUNT", (right_x, pollen_y), yellow)
        pollen_y += 30

        pollen_data = [
            ("Tree", "LOW"),
            ("Grass", "MODERATE"),
            ("Weed", "LOW"),
            ("Mold", "HIGH"),
        ]
        for pollen_type, level in pollen_data:
            _blit(surface, ctx, "tiny", f"{pollen_type}:", (right_x, pollen_y), white)

            if level == "HIGH":
                color = _SOFT_RED
            elif level == "MODERATE":
                color = yellow
            else:
                color = _SOFT_GREEN

            bar_x = right_x + 70
            bar_width = 80 if level == "HIGH" else 60 if level == "MODERATE" else 40
            pygame.draw.rect(surface, color, (bar_x, pollen_y + 2, bar_width, 12))

            text_x = bar_x + bar_width + 10
            _blit(surface, ctx, "tiny", level, (text_x, pollen_y), color)
            pollen_y += 25

        y_pos = max(y_pos, pollen_y) + 20
        font_normal = _font(ctx, "normal")
        if font_normal is not None:
            tips_title = font_normal.render("HEALTH RECOMMENDATIONS", True, yellow)
            surface.blit(tips_title, tips_title.get_rect(center=(320, y_pos)))
        y_pos += 25

        tips = [
            "Air quality is good for outdoor activities",
            "High mold count - allergy sufferers take precaution",
            "UV index moderate - use sunscreen if outside",
        ]

        clip_rect = pygame.Rect(60, y_pos, 520, 440 - y_pos)
        surface.set_clip(clip_rect)

        total_height = len(tips) * 22
        visible_height = 440 - y_pos

        offset = getattr(self, "_scroll_offset", 0.0)
        direction = getattr(self, "_scroll_dir", 1.0)
        if total_height > visible_height:
            offset += direction * dt * 30.0
            if offset > 0:
                offset = 0.0
                direction = -1.0
            elif offset < -(total_height - visible_height):
                offset = -(total_height - visible_height)
                direction = 1.0
            self._scroll_offset = offset
            self._scroll_dir = direction

        font_tiny = _font(ctx, "tiny")
        tip_y = y_pos + offset
        for tip in tips:
            if font_tiny is None:
                break
            if font_tiny.size(tip)[0] > _MAX_TIP_WIDTH:
                for line in _wrap(font_tiny, tip, _MAX_TIP_WIDTH):
                    if 0 < tip_y < 440:
                        _blit(surface, ctx, "tiny", f"\u2022 {line}", (70, tip_y), white)
                    tip_y += 20
            else:
                if 0 < tip_y < 440:
                    _blit(surface, ctx, "tiny", f"\u2022 {tip}", (70, tip_y), white)
                tip_y += 22

        surface.set_clip(None)

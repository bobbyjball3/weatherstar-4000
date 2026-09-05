"""Stock Market screen: index quotes from the stocks datasource.

The legacy screen embedded an Alpha Vantage API key in source; the plugin
architecture never does.  Quotes arrive via the configured ``stocks``
datasource (which owns its own API key configuration).
"""

from __future__ import annotations

from typing import Any

import pygame

from weatherstar_4000 import render
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen

_GREEN = (0, 255, 0)
_RED = (255, 0, 0)

#: Legacy display names for the symbols tracked by the default datasource.
_SYMBOL_NAMES = {
    "DIA": "DOW JONES",
    "SPY": "S&P 500",
    "QQQ": "NASDAQ",
}


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


def _format_price(value: Any) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _format_change(value: Any) -> tuple[str, tuple[int, int, int]]:
    try:
        change = float(value)
    except (TypeError, ValueError):
        return "N/A", _GREEN
    sign = "+" if change >= 0 else ""
    color = _GREEN if change >= 0 else _RED
    return f"{sign}{change:,.2f}", color


@plugin
class StockMarketScreen(Screen):
    name = "stock_market"
    media = ("backgrounds", "fonts", "logos")
    datasources = ("stocks",)

    def draw(self, surface: pygame.Surface, ctx: Any, dt: float) -> None:
        render.draw_background(surface, ctx, "5")
        render.draw_header(surface, ctx, "Stock Market", "Update")

        yellow = _color(ctx, "yellow", (255, 255, 0))
        white = _color(ctx, "white", (255, 255, 255))
        normal = _font(ctx, "normal", 20)

        y_pos = 150
        title = _font(ctx, "extended", 24).render("MARKET INDICES", True, yellow)
        surface.blit(title, title.get_rect(center=(320, y_pos)))
        y_pos += 50

        quotes: list[dict] = []
        ds = _ds(ctx, "stocks")
        if ds is not None:
            try:
                quotes = list(ds.quotes() or [])
            except Exception:  # noqa: BLE001 - data is optional
                quotes = []

        if not quotes:
            message = normal.render("Market data unavailable", True, white)
            surface.blit(message, message.get_rect(center=(320, 240)))
            return

        for quote in quotes:
            symbol = str(quote.get("symbol") or "")
            name = _SYMBOL_NAMES.get(symbol, symbol)
            price = _format_price(quote.get("price"))
            change, color = _format_change(quote.get("change"))
            percent = _format_change(quote.get("change_percent"))[0]

            name_text = normal.render(name, True, white)
            price_text = normal.render(price, True, white)
            change_text = normal.render(change, True, color)
            percent_text = normal.render(percent, True, color)

            surface.blit(name_text, (100, y_pos))
            price_rect = price_text.get_rect(right=400, y=y_pos)
            surface.blit(price_text, price_rect)
            surface.blit(change_text, (440, y_pos))
            percent_rect = percent_text.get_rect(right=590, y=y_pos)
            surface.blit(percent_text, percent_rect)
            y_pos += 40

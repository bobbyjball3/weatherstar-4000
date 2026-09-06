"""Stock Market screen: index quotes from the stocks datasource.

The legacy screen embedded an Alpha Vantage API key in source; the plugin
architecture never does.  Quotes arrive via the configured ``stocks``
datasource (which owns its own API key configuration) as typed ``Quote`` rows
and are rendered through the shared data_table component; price/change
formatting and up/down coloring live in the component's column formatters.
"""

from __future__ import annotations

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.components.data_table import Column
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen


@plugin
class StockMarketScreen(Screen):
    name = "stock_market"
    media = ("backgrounds", "fonts", "logos")
    datasources = ("stocks",)

    layout = (
        ComponentSpec(component="background", config={"background_name": "5"}),
        ComponentSpec(
            component="header",
            config={"title_top": "Stock Market", "title_bottom": "Update", "has_noaa": False},
        ),
        ComponentSpec(component="clock"),
        ComponentSpec(
            component="data_table",
            config={
                "datasource_name": "stocks",
                "rows_method": "quotes",
                "scroll": False,
                "max_rows": 8,
                "start_y": 130,
                "empty_text": "Market data unavailable",
                "columns": [
                    Column(header="INDEX", header_x=60, x=60, format="text", attr="display_name"),
                    Column(header="PRICE", header_x=300, x=300, format="money", attr="price"),
                    Column(
                        header="CHANGE",
                        header_x=420,
                        x=430,
                        format="signed",
                        attr="change",
                        sign_color=True,
                    ),
                    Column(
                        header="CHG%",
                        header_x=520,
                        x=530,
                        format="signed",
                        attr="change_percent",
                        sign_color=True,
                    ),
                ],
            },
        ),
    )

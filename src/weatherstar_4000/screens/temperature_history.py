"""30-Day Temperature History screen (port of legacy ``draw_temperature_history``).

Composes a scrolling DATE / HIGH / LOW ``data_table`` that row-jumps in classic
WeatherStar style when more than eight rows are present.
"""

from __future__ import annotations

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.components.data_table import Column
from weatherstar_4000.registry import plugin
from weatherstar_4000.screen import Screen


@plugin
class TemperatureHistoryScreen(Screen):
    name = "temperature_history"
    media = ("backgrounds",)
    datasources = ("history",)
    layout = (
        ComponentSpec(component="background", config={"background_name": "5"}),
        ComponentSpec(
            component="header", config={"title_top": "30-Day", "title_bottom": "Temperature"}
        ),
        ComponentSpec(component="clock"),
        ComponentSpec(
            component="data_table",
            config={
                "datasource_name": "history",
                "rows_method": "temperature",
                "scroll_offset_index": 0,
                "max_rows": 8,
                "empty_text": "History data unavailable",
                "columns": [
                    Column(header="DATE", header_x=60, x=60, format="date", index=0),
                    Column(header="HIGH", header_x=320, x=330, format="degrees", index=1),
                    Column(header="LOW", header_x=480, x=490, format="degrees", index=2),
                ],
            },
        ),
    )

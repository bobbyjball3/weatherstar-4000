"""UV Index Forecast screen (port of legacy ``draw_uv_index``).

Renders a DATE / UV INDEX / PROTECTION table from the ``uv_index`` datasource
rows using the datasource's static protection-level classification.
"""

from __future__ import annotations

from weatherstar_4000.components.base import ComponentSpec
from weatherstar_4000.components.data_table import Column
from weatherstar_4000.registry import plugin
from weatherstar_4000.screens.base import Screen


@plugin
class UvIndexScreen(Screen):
    name = "uv_index"
    media = ("backgrounds",)
    datasources = ("uv_index",)
    layout = (
        ComponentSpec(component="background", config={"background_name": "5"}),
        ComponentSpec(
            component="header", config={"title_top": "UV Index", "title_bottom": "Forecast"}
        ),
        ComponentSpec(component="clock"),
        ComponentSpec(
            component="data_table",
            config={
                "datasource_name": "uv_index",
                "rows_method": "daily",
                "scroll": False,
                "max_rows": 7,
                "empty_text": "UV Index data unavailable",
                "columns": [
                    Column(header="DATE", header_x=60, x=60, format="date", key="date"),
                    Column(header="UV INDEX", header_x=280, x=300, format="int", key="uv_index"),
                    Column(
                        header="PROTECTION",
                        header_x=450,
                        x=460,
                        format="protection",
                        key="uv_index",
                    ),
                ],
            },
        ),
    )

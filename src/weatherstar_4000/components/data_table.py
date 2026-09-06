"""DataTable component: columnar table with classic row-jump scrolling.

Owns the shared table layout (header row, underline, spaced data rows) plus the
classic WeatherStar row-jump scroll: when there are more than ``max_rows``, the
visible window is derived from the datasource's ``scroll_offsets`` and advanced
by calling ``datasource.scroll(time.time())`` each frame.

Rows come from ``datasource_name.rows_method(lat, lon)`` (tuple rows for
history screens, dict rows for uv_index).  Each :class:`Column` selects a cell
by ``index`` or ``key`` and renders it with a named formatter.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal

import pygame
from pydantic import BaseModel, ConfigDict, Field, model_validator

from weatherstar_4000.components.base import Component
from weatherstar_4000.registry import plugin

if TYPE_CHECKING:
    from weatherstar_4000.context import AppContext

_HEADER_GAP = 40
_ROW_GAP = 30
_UNDERLINE_X = (50, 590)


class Column(BaseModel):
    """One data column: header placement, cell accessor, and formatter."""

    model_config = ConfigDict(extra="forbid")

    header: str = Field(description="Header text for this column.")
    header_x: int = Field(description="Left x of the header cell.")
    x: int = Field(description="Left x of the data cells.")
    format: Literal["date", "degrees", "int", "text", "inches", "precip_status", "protection"] = (
        Field(description="How to render the raw cell value.")
    )
    index: int | None = Field(default=None, description="Cell position for tuple rows.")
    key: str | None = Field(default=None, description="Cell dict key for dict rows.")
    attr: str | None = Field(default=None, description="Cell attribute for typed model rows.")

    @model_validator(mode="after")
    def _exactly_one_accessor(self) -> Column:
        present = sum(accessor is not None for accessor in (self.index, self.key, self.attr))
        if present != 1:
            raise ValueError(
                "Column needs exactly one of `index` (tuple rows), `key` (dict rows) "
                "or `attr` (model rows)."
            )
        return self


@plugin
class DataTable(Component):
    """Columnar, optionally row-jump-scrolling data table."""

    name = "data_table"

    datasource_name: str = Field(description="Datasource whose rows this table shows.")
    rows_method: str = Field(description="Datasource method called with (lat, lon) to fetch rows.")
    columns: list[Column] = Field(description="Ordered column definitions.")
    scroll_offset_index: int = Field(
        default=0, description="Index into datasource scroll_offsets used when scrolling."
    )
    scroll: bool = Field(
        default=True,
        description="Advance via datasource.scroll() when rows exceed max_rows.",
    )
    max_rows: int = Field(default=8, description="Rows visible before scrolling engages.")
    start_y: int = Field(default=120, description="Top of the header row.")
    empty_text: str = Field(default="Data unavailable", description="Centered empty message.")

    def step(self, ctx: AppContext, dt: float) -> None:
        if not self.scroll:
            return
        ds = self.datasource(ctx, self.datasource_name)
        if ds is None or not callable(getattr(ds, "scroll", None)):
            return
        rows = self._fetch(ctx)
        if rows and len(rows) > self.max_rows:
            try:
                ds.scroll(time.time())
            except Exception:  # noqa: BLE001 - scrolling is best-effort
                pass

    def render(self, surface: pygame.Surface, ctx: AppContext) -> None:
        rows = self._fetch(ctx)
        if not rows:
            self.centered(surface, ctx, self.empty_text, 240, font_name="normal")
            return

        yellow = self.color(ctx, "yellow")
        white = self.color(ctx, "white")
        font = self.font(ctx, "normal")

        y_pos = self.start_y
        for column in self.columns:
            surface.blit(font.render(column.header, True, yellow), (column.header_x, y_pos))
        y_pos += _HEADER_GAP

        pygame.draw.line(
            surface, yellow, (_UNDERLINE_X[0], y_pos - 5), (_UNDERLINE_X[1], y_pos - 5), 1
        )

        start = self._start_index(ctx, rows)
        for row in rows[start : start + self.max_rows]:
            cells = []
            for column in self.columns:
                text = self._format_cell(self._cell(row, column), column, ctx)
                if text is None:
                    break
                cells.append(text)
            else:
                for column, text in zip(self.columns, cells):
                    surface.blit(font.render(text, True, white), (column.x, y_pos))
                y_pos += _ROW_GAP

    # -- internals --------------------------------------------------------

    def _fetch(self, ctx: AppContext) -> list[Any]:
        ds = self.datasource(ctx, self.datasource_name)
        if ds is None or not callable(getattr(ds, self.rows_method, None)):
            return []
        lat, lon = self.latlon(ctx)
        try:
            rows = getattr(ds, self.rows_method)(lat, lon)
        except Exception:  # noqa: BLE001 - datasource rows are optional
            return []
        return list(rows or [])

    def _start_index(self, ctx: AppContext, rows: list[Any]) -> int:
        if not self.scroll:
            return 0
        extra = len(rows) - self.max_rows
        if extra <= 0:
            return 0
        ds = self.datasource(ctx, self.datasource_name)
        offset = 0.0
        if ds is not None:
            try:
                offset = float(ds.scroll_offsets[self.scroll_offset_index])
            except Exception:  # noqa: BLE001 - treat missing offsets as 0
                offset = 0.0
        return (int(offset / 30.0)) % (extra + 1)

    @staticmethod
    def _cell(row: Any, column: Column) -> Any:
        if column.index is not None:
            try:
                return row[column.index]
            except (IndexError, TypeError):
                return None
        if column.key is not None:
            try:
                return row.get(column.key) if isinstance(row, dict) else None
            except AttributeError:
                return None
        try:
            return getattr(row, column.attr)
        except (AttributeError, TypeError):
            return None

    def _format_cell(self, raw: Any, column: Column, ctx: AppContext) -> str | None:
        if raw is None or raw == "":
            return None
        fmt = column.format
        try:
            if fmt == "date":
                return self.format_date(raw)
            if fmt == "degrees":
                return f"{int(float(raw))}\u00b0"
            if fmt == "int":
                return str(int(float(raw)))
            if fmt == "text":
                return str(raw)
            if fmt == "inches":
                value = float(raw)
                return "Trace" if value == 0 else f'{value:.2f}"'
            if fmt == "precip_status":
                value = float(raw)
                if value == 0:
                    return "Dry"
                if value < 0.1:
                    return "Light"
                if value < 0.5:
                    return "Moderate"
                return "Heavy"
            if fmt == "protection":
                return self._protection(ctx, float(raw))
        except (TypeError, ValueError):
            return None
        return str(raw)

    def _protection(self, ctx: AppContext, uv_value: float) -> str:
        uv_ds = self.optional_datasource(ctx, "uv_index")
        if uv_ds is not None and callable(getattr(uv_ds, "protection_level", None)):
            try:
                return uv_ds.protection_level(uv_value)
            except (TypeError, ValueError):
                pass
        if uv_value <= 2:
            return "Low"
        if uv_value <= 5:
            return "Moderate"
        if uv_value <= 7:
            return "High"
        if uv_value <= 10:
            return "Very High"
        return "Extreme"

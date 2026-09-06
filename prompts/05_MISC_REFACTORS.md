# Misc. Refactors

I want to refactor various parts of the app where the code is messy or overly complex.

## Decisions (from brainstorming)

- **Data contracts:** datasources return typed Pydantic models. Two return shapes:
  - `list[X]` for homogeneous rows (empty list = no data).
  - `X | None` for a single "widget"/snapshot result (`None` = unavailable → NO DATA),
    or `X` with empty defaults for lookups (e.g. `get_city`).
  - No consumer does metaprogramming across datasources, so no shared envelope is
    needed; type hints tell the consumer which shape it holds.
- **Datasources own their public contract**, which need not match the upstream API
  shape. All messy/defensive parsing lives at the HTTP boundary inside the
  datasource; consumers trust the returned models.
- **Delivery:** phased (A → B → C below), each leaving `task check` + `task coverage`
  green so each phase can be validated lightly. Themes is a separate, later effort.
- **Dependencies:** open to adding a library if it materially simplifies a part of
  the app; no candidates beyond pydantic (already in use) identified yet.

## Phase A — data contracts

- **Datasource models** (co-located in the module that returns them):
  - `noaa.py`: `CurrentConditions`, `ForecastPeriod`, `HourlyPeriod`, `City` →
    `get_current → CurrentConditions | None`, `get_forecast → list[ForecastPeriod]`,
    `get_hourly → list[HourlyPeriod]`, `get_city → City`.
  - `feeds.py`: `Quote` (+ `direction`), `Alert`, `Earthquake`, `UvReading`.
  - `history.py`: `TemperatureRow`, `PrecipRow` (keep `scroll`/`scroll_offsets`).
  - `news.py`: `Headline`; `city_name → str`.
  - `radar.py`: unchanged (`list[Surface]`).
- **renderer.py:** remove the NOAA-specific helpers (`num`, `measure`, `text`,
  `period_start_date`) — they leak the upstream contract into screens. Fold that
  logic into the models. Keep generic `fahrenheit` / `cardinal` / `format_date` /
  icon helpers.
- **Datasource access:** make `Renderer.datasource()` strict (raise on unknown —
  accessing an undeclared datasource is a bug and should crash, not degrade to
  "no data"). Add `optional_datasource()` for genuinely optional reads (ticker,
  `local_news._resolve_city`, `data_table` UV-protection fallback).
- **Screens/components:** replace `.get()` soup and `self.num(...)` with typed
  attribute access; `data_table.Column` gains an attribute accessor.
- **Effective-config logging:** add a logger to `Plugin`; log masked effective
  config in `from_config` (components log the merged scope + per-instance config).

## Phase B — config unification

- Model `[location]`, `[video]`, `[logging]` as Pydantic models in `config_file.py`
  (single source of truth), replacing the hand-built dicts in `config_file.py` and
  the parallel `_*_COMMENTS`/`_*_DEFAULTS` dicts in `skeleton.py`. `skeleton.py`
  generates those sections from the model fields.
- **Remove `auto_detect`** (parsed but never used; the user supplies lat/lon).
- Update `engine.resolve_location` / `cli` to typed attributes; regenerate
  `docs/CONFIGURATION.md`.

## Phase C — presentation

- **`_icon_for_token`:** replace the if/elif cascade with an ordered list of
  `_IconRule` dataclasses (exact-match map + ordered rules with any/all/none
  substrings and day/night names). Flat and table-testable rather than a nested
  recursive decision tree.
- **Componentization rule:** a screen's `compose` may only *place* discrete visual
  blocks; it may not transform/format data. Extract `current_conditions`
  observation rows and `stock_market` into `data_table` placements; move
  formatting (price/change, ceiling/visibility/pressure strings) into the models.

## Cross-cutting

- Update the rich/no-data test stubs to return models instead of raw NOAA dicts.
- Strict datasource access will surface any screen reading an *undeclared*
  datasource — fix those `datasources = (...)` declarations.
- Keep tests offline and deterministic.

## Deferred — themes (Phase D)

- **Approach:** parameterized screens/components, not parallel implementations. A
  "theme" is a *bundle* (color palette + fonts + backgrounds + logos + icons +
  default sequence), selected by config. Screens never branch on theme name; they
  read named colors/fonts/assets and the bundle supplies them.
- **Front-load now:** de-hardcode colors/fonts/sizes across screens/components
  (e.g. `stock_market` `_GREEN`/`_RED`, `ticker` banner color, AQI/radar palettes)
  and route them through `ctx.colors` / theme keys with semantic keys
  (`up`, `down`, `severe`, `banner_bg`).

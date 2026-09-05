# Architecture

This document explains how the WeatherStar 4000 v2 engine is put together.
Everything lives under `src/weatherstar_4000/v2/`.

## At a glance

The app renders a timed, looping sequence of **screens** on a pygame surface.
Each screen is a *plugin* that declares which **datasources** feed it, which
**media** (fonts, backgrounds, logos, icons, music) it decorates itself with,
and any per-plugin configuration. At runtime the **engine** reads a TOML config,
instantiates the referenced plugins, wires a shared **context**, and drives the
render loop; a bottom **ticker** crawls across every screen and music plays in
the background.

```
        config.toml ──► AppConfig ──► Builder ──► AppContext/DataRegistry
        (XDG/env/CLI)     │                 │            │
                          ▼                 ▼            ▼
                   sequence chosen      plugins      screens built &
                   from [sequences.*]  instantiated   prepared
                                                    │
                         run_sequence ◄─────────────┘
                       (render loop, 30 fps)
                          │      │
                 per-slide pause   ticker overlay  (BottomTicker)
                          │      └── music advance (Builder.advance_music)
                          ▼
                   pygame.display.flip()
```

## The five plugin kinds

Every plugin is a subclass of `Plugin` (in `plugin.py`), which is itself a
Pydantic `BaseModel`. Plugins self-register with the `@plugin` decorator and are
grouped by `kind`:

| Kind | Base class | Example | Purpose |
| --- | --- | --- | --- |
| `screen` | `Screen` | `radar`, `current_conditions` | One full-screen "display" |
| `component` | `Component` | `header`, `background`, `clock` | Reusable renderers placed on screens |
| `media` | `Media` | `fonts`, `backgrounds`, `icons`, `music` | Loads local assets into the context |
| `datasource` | `Datasource` | `weather`, `history`, `stocks` | Fetches data behind a typed API |
| `sequence` | (config-declared) | `main` | Named ordered run of screens |

### Screens

`Screen` (in `screen.py`) subclasses declare metadata as `ClassVar`s —
`components`, `datasources`, `media`, `background` — so Pydantic never treats
them as config fields. Concrete screens implement `draw(surface, ctx, dt)`;
animated screens can also implement `step(ctx, dt)` / `prepare(ctx)`. Screens
are deliberately defensive: they read data through helpers that catch and
degrade to a "no data" message, so a missing or slow datasource never crashes
the show.

### Components

`Component` (in `component.py`) is the smallest composable renderer. The
engine builds a screen's declared components and exposes them under
`ctx.assets["components"]`. Example: the `header` component draws the yellow
title, clock/date and optional NOAA mark used by most screens.

### Media

`Media` plugins load local assets from an `asset_dir` (default
`static_assets/…`) and register them on the context:

- `fonts` → `ctx.fonts` (named `pygame.font.Font` objects)
- `backgrounds` / `logos` / `icons` → `ctx.assets` dicts plus
  `ctx.assets["icon_manager"]`
- `music` → discovers tracks; playback is *owned by the engine*, not the media
  plugin (see below).

### Datasources

`Datasource` (in `datasource.py`) is a `Plugin` with common config
(`timeout`, `user_agent`) and HTTP plumbing shared by all feeds:

- a `requests.Session` built lazily per instance with the configured
  `User-Agent` and any auth derived from sensitive fields (`_session_for`);
- `http_get_json(...)` with timeout, status logging and graceful `None` on
  failure;
- a tiny TTL cache (`cache_get` / `cache_set`) so screens can poll cheaply.

Auth fields typed as Pydantic `SecretStr` (e.g. `stocks.api_key`) are unwrapped
only at the point of use (`get_secret_value()`), and query-param style keys
(`api_key_param`) are injected per request via `_query_params`.

## Registry and discovery

`registry.py` holds a process-wide `PluginRegistry` mapping
`(kind, name) -> class`. Built-ins are discovered by importing every module in
the `v2` sub-packages (`v2/plugins/__init__.py` walks `screens`, `components`,
`media`, `datasources`, `sequences`). External plugins register through entry
points in the `weatherstar4000.plugins` group. `registry.discover()` is
idempotent and is called once by the engine/CLI.

## Configuration

Config is loaded by `config_file.py` (`AppConfig`) and applied per plugin via
Pydantic:

- The file is discovered from `--config` > `WEATHERSTAR_CONFIG` >
  `~/.config/weatherstar4000/config.toml` (`xdg_config_file`).
- `AppConfig.scope(kind, name)` returns the `[<kind>.<name>]` section, which
  `Plugin.from_config(...)` feeds to `model_validate`. Missing required fields
  raise `InvalidConfiguration` with the offending scope and a TOML example.
- Non-plugin sections (`sequence`, `[location]`, `[video]`, `[logging]`,
  `[sequences.*]`) are read by small typed accessors on `AppConfig`.

Because plugins are Pydantic models with `Field(description=...)` annotations,
`skeleton.py` can generate a fully commented example config
(`weatherstar4000-v2 generate-config`) — descriptions are rendered inline as
`#` comments, and required/secret fields appear as commented `# key = "value"`
placeholders. See `docs/CONFIGURATION.md`.

## Context

`context.py` provides the objects threaded through rendering:

- `Location` — resolved lat/lon/label.
- `DataRegistry` — named `Datasource` instances the screens read through
  (`ctx.data.get("weather")`).
- `AppContext` — surface, theme, `fonts`, `assets`, `icon_manager`,
  `location`, and conveniences (`colors`, `font`, `asset`, `size`). It replaces
  the old monolithic `ws` object; screens never reach into a god object.

Themes live in `v2/themes.py` (a `ColorTheme` + a set of named palettes).
`AppContext.colors` merges the selected theme over the classic palette so a
missing key still has a sensible value.

## Engine

`engine.py` contains the two main pieces:

- `Builder` resolves the sequence, then constructs every referenced plugin from
  config: `build_data`, `build_media`, `build_components`, `build_screens`, and
  `build_context`, which assembles the fully-populated `AppContext` for the
  run. It also owns music lifecycle (`start_music`, `advance_music`,
  `stop_music`).
- `run_sequence(...)` is the render loop (30 fps by default). Each frame it
  steps and draws the current slide, advances on the slide's `pause`, wraps
  around forever in interactive mode (or does one pass in non-interactive
  mode), draws the `BottomTicker`, polls the music controller, and flips the
  display.

`SequenceRunner.validate(...)` reuses the built screens but only *draws* each
slide once headlessly (no window, datasources usually stubbed) — this powers
`weatherstar4000-v2 --validate` and the integration tests.

### Bottom ticker

`ticker.py` (`BottomTicker`) draws the authentic navy banner + white crawling
text over the bottom of every screen. Content is rebuilt from the `weather`
datasource on an interval (`+++ CITY, STATE +++`, current conditions, today /
tonight) with a static fallback.

### Music

Music is **ambient and config-driven**, not a screen dependency: when
`[media.music] enabled = true` the engine includes the `music` media, shuffles
the discovered tracks, starts a random first song, and advances through the
shuffle as each track ends (`Music.advance`, polled every frame). Loading
headless/validate never starts audio.

## Logging

`logging_setup.py` configures structlog over stdlib logging with severity-ANSI
console output, an optional JSON-lines file sink, and a redaction processor that
masks sensitive keys and any `SecretStr` values — so credentials never reach
logs.

## Headless testing

`tests/conftest.py` forces SDL dummy drivers before pygame imports, so the whole
suite (and `--validate`) runs on CI machines without a display. External APIs
are never hit in tests: datasource tests monkeypatch `http_get_json`, and the
integration test swaps the real `DataRegistry` for benign stubs.

## Key design decisions

- **Plugins are Pydantic models.** Typed fields replace hand-rolled config
  descriptors: validation, coercion, defaults and JSON schema come for free,
  and `Field(description=...)` drives generated documentation.
- **Non-config metadata is `ClassVar`.** `kind`, `name`, `media`,
  `datasources`, etc. are annotated `ClassVar` so they never become config
  fields.
- **Secrets are `SecretStr`.** They are masked in `repr`/`str` and by the log
  redactor, and unwrapped only at the HTTP boundary.
- **Runtime state is `PrivateAttr`.** Pydantic forbids undeclared attributes, so
  engine-injected state (sessions, caches, scroll offsets, playlist) is declared
  as private attributes.
- **Config discovery is standard-library.** `--config` > env var > XDG file,
  and plugin discovery via importlib entry points — no framework needed.
- **Rendering is defensive.** Every datasource read is wrapped; missing data
  renders a "NO DATA" message rather than crashing the loop.

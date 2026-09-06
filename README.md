# Weather Star

A recreation of The Weather Channel's Weather Star local forecast
presentation — the 1990s Weather Star 4000 and the Weather Star 3000 are both
available as built-in themes.

## What it is

`weatherstar` renders the classic Weather Star local forecast show — current
conditions, radar, forecasts, news and more — using pygame. The app is
plugin-driven: every screen, datasource, media type and component is a
discoverable plugin with typed, documented configuration. A theme swaps the
whole visual identity: colors, fonts, assets, and the layout era
(`weatherstar4000` by default, `weatherstar3000` for the 3000 look).

## Running the app

Requires Python 3.10 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync

# Create a commented config (see docs/CONFIGURATION.md), then run:
uv run weatherstar --config ~/.config/weatherstar/config.toml

# Or run ad hoc with command-line location + a built-in default sequence:
uv run weatherstar --sequence main --lat 28.5383 --lon -81.3792
```

Useful flags:

| Flag | Purpose |
| --- | --- |
| `--config PATH` | Config file (default `~/.config/weatherstar/config.toml`) |
| `--theme NAME` | Visual theme (`weatherstar4000`, `weatherstar3000`, …) |
| `--sequence NAME` | Sequence to run (defaults from config) |
| `--lat` / `--lon` | Location coordinates |
| `--validate` | Headless: render every slide once and report failures |
| `generate-config` | Emit a commented config skeleton to stdout or `-o PATH` |

Run `weatherstar --help` for the full list.

## Documentation

| Doc | Contents |
| --- | --- |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Configuring the app — with a fully commented example config |
| [docs/THEMES.md](docs/THEMES.md) | Themes: the 3000/4000 looks and how to add your own |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the plugin engine is put together |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Tooling, tests, CI, and the dev workflow |

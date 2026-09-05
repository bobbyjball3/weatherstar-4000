# WeatherStar 4000

A recreation of The Weather Channel's iconic 1990s WeatherStar 4000 local
forecast presentation.

> **Note:** the original README (features, controls, packaging, Raspberry Pi
> setup, etc.) has been preserved as [`README.old.md`](./README.old.md). This
> README is a brief orientation; see the **Documentation** links below for
> everything else.

## What it is

`weatherstar-4000` renders the classic 90s-style WeatherStar local forecast
show — current conditions, radar, forecasts, news and more — using pygame. The
app is plugin-driven: every screen, datasource, media type and component is a
discoverable plugin with typed, documented configuration.

## Running the app

Requires Python 3.10 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync

# Create a commented config (see docs/CONFIGURATION.md), then run:
uv run weatherstar4000 --config ~/.config/weatherstar4000/config.toml

# Or run ad hoc with command-line location + a built-in default sequence:
uv run weatherstar4000 --sequence main --lat 28.5383 --lon -81.3792
```

Useful flags:

| Flag | Purpose |
| --- | --- |
| `--config PATH` | Config file (default `~/.config/weatherstar4000/config.toml`) |
| `--sequence NAME` | Sequence to run (defaults from config) |
| `--lat` / `--lon` | Location coordinates |
| `--validate` | Headless: render every slide once and report failures |
| `generate-config` | Emit a commented config skeleton to stdout or `-o PATH` |

Run `weatherstar4000 --help` for the full list.

## Documentation

| Doc | Contents |
| --- | --- |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Configuring the app — with a fully commented example config |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the plugin engine is put together |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Tooling, tests, CI, and the dev workflow |

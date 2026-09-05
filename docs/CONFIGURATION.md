# WeatherStar 4000 v2 — Configuration

The v2 engine reads one TOML file that configures the plugin graph: which
sequence to run, where to point the datasources, window/logging behavior, and
overrides for any plugin's typed config fields.

## Where the file lives

| Source | Path / value |
| --- | --- |
| `--config` CLI flag | explicit path |
| `WEATHERSTAR_CONFIG` | explicit path |
| Default (XDG) | `~/.config/weatherstar4000/config.toml` |

A config file is **not** required if you pass `--sequence`, `--lat` and `--lon`
on the command line.

## Generating a skeleton

Every configurable value is declared on the plugin classes with a description,
so you can always regenerate a fully commented starting point that stays in sync
with the code:

```sh
uv run weatherstar4000-v2 generate-config --sequence main -o ~/.config/weatherstar4000/config.toml
```

Fill in any `# REQUIRED` keys and uncomment the values you want to change.

## Precedence

* **Sequence**: `--sequence` > `WEATHERSTAR_SEQUENCE` > the top-level
  `sequence` key.
* **Location**: `--lat`/`--lon` > the `[location]` section.
* **Plugin scopes** (`[datasource.*]`, `[media.*]`, `[component.*]`,
  `[screen.*]`) are matched by plugin `kind.name`; each overrides that plugin's
  declared defaults.

## Example

Below is the output of `weatherstar4000-v2 generate-config --sequence main`
with the location filled in for Orlando, FL. Every value is documented inline.

```toml
# WeatherStar 4000 v2 configuration skeleton.
# Generated per-plugin from declared typed config fields.
# Every configurable value is documented inline; uncomment keys you want
# to change and fill in REQUIRED values.

# Sequence to execute (override with --sequence or WEATHERSTAR_SEQUENCE).
sequence = "main"

[location]
# Latitude used to center weather data (e.g. 28.5383).
lat = 28.5383
# Longitude used to center weather data (e.g. -81.3792).
lon = -81.3792
# Human-readable location label shown on screen (optional).
description = "Orlando, FL"
# Attempt automatic location detection when no lat/lon given.
auto_detect = true

[video]
# Window width in pixels.
width = 640
# Window height in pixels.
height = 480
# Target frames per second.
fps = 30

[sequences.main]
# Default seconds each slide is shown (per-slide `pause` overrides).
pause = 15.0
slides = [
    { screen = "air_quality" },
    { screen = "almanac" },
    { screen = "current_conditions" },
    { screen = "earthquakes" },
    { screen = "extended_forecast" },
    { screen = "hazards" },
    { screen = "hourly_forecast" },
    { screen = "local_forecast" },
    { screen = "local_news" },
    { screen = "marine_forecast" },
    { screen = "monthly_outlook" },
    { screen = "msn_news" },
    { screen = "precipitation_history" },
    { screen = "progress" },
    { screen = "radar" },
    { screen = "reddit_news" },
    { screen = "regional_observations" },
    { screen = "severe_weather_alert" },
    { screen = "stock_market" },
    { screen = "sun_moon" },
    { screen = "temperature_graph" },
    { screen = "temperature_history" },
    { screen = "travel_cities" },
    { screen = "uv_index" },
    { screen = "weather_records" },
    { screen = "weekend_forecast" },
    { screen = "wind_pressure" },
]

[datasource.alerts]
# HTTP request timeout in seconds.
timeout = 10
# User-Agent header sent with upstream API requests.
user_agent = "WeatherStar4000/v2 (python)"
# Colon-separated severity order used to sort alerts (most severe first).
severity_priority = "extreme:severe:moderate"

[datasource.earthquakes]
# HTTP request timeout in seconds.
timeout = 10
# User-Agent header sent with upstream API requests.
user_agent = "WeatherStar4000/v2 (python)"
# Minimum earthquake magnitude to include.
min_magnitude = 3.0
# Maximum number of earthquakes to fetch.
limit = 10

[datasource.history]
# HTTP request timeout in seconds.
timeout = 10
# User-Agent header sent with upstream API requests.
user_agent = "WeatherStar4000/v2 (python)"

[datasource.local_news]
# HTTP request timeout in seconds.
timeout = 10
# User-Agent header sent with upstream API requests.
user_agent = "WeatherStar4000/v2 (python)"

[datasource.radar]
# HTTP request timeout in seconds.
timeout = 10
# User-Agent header sent with upstream API requests.
user_agent = "WeatherStar4000/v2 (python)"

[datasource.stocks]
# HTTP request timeout in seconds.
timeout = 10
# User-Agent header sent with upstream API requests.
user_agent = "WeatherStar4000/v2 (python)"
# Alpha Vantage API key (required; sent with each request).
# REQUIRED - supply a value for this key.
# api_key = "value"
# Query parameter the API key is sent under.
api_key_param = "apikey"
# Header the API key is sent under instead (leave blank to use the query parameter).
api_key_header = ""
# Comma-separated stock/index symbols to display.
symbols = "DIA,SPY,QQQ"

[datasource.uv_index]
# HTTP request timeout in seconds.
timeout = 10
# User-Agent header sent with upstream API requests.
user_agent = "WeatherStar4000/v2 (python)"
# Number of days of UV index forecast to fetch.
days = 7

[datasource.weather]
# HTTP request timeout in seconds.
timeout = 10
# User-Agent header sent with upstream API requests.
user_agent = "WeatherStar4000/v2 (python)"

[media.backgrounds]
# Directory containing this media's assets (project-relative or absolute).
asset_dir = "static_assets"

[media.fonts]
# Directory containing this media's assets (project-relative or absolute).
asset_dir = "static_assets"

[media.icons]
# Directory containing this media's assets (project-relative or absolute).
asset_dir = "static_assets"

[media.logos]
# Directory containing this media's assets (project-relative or absolute).
asset_dir = "static_assets"

[media.music]
# Directory containing this media's assets (project-relative or absolute).
asset_dir = "static_assets"
# Play background music during the show.
enabled = false
# Music volume, from 0.0 (silent) to 1.0 (full).
volume = 0.6

[component.background]
# Background asset key to fill the screen (e.g. '1'..'6').
background_name = "1"

[component.clock]

[component.header]
# Top line of the screen header.
title_top = "WeatherStar"
# Bottom line of the screen header.
title_bottom = "4000"
# Show the NOAA mark to the right of the header title.
has_noaa = false

[screen.air_quality]

[screen.almanac]

[screen.current_conditions]

[screen.earthquakes]

[screen.extended_forecast]

[screen.hazards]

[screen.hourly_forecast]

[screen.local_forecast]

[screen.local_news]

[screen.marine_forecast]

[screen.monthly_outlook]

[screen.msn_news]

[screen.precipitation_history]

[screen.progress]

[screen.radar]

[screen.reddit_news]

[screen.regional_observations]

[screen.severe_weather_alert]

[screen.stock_market]

[screen.sun_moon]

[screen.temperature_graph]

[screen.temperature_history]

[screen.travel_cities]

[screen.uv_index]

[screen.weather_records]

[screen.weekend_forecast]

[screen.wind_pressure]

[logging]
# Minimum log level: DEBUG, INFO, WARNING, ERROR or CRITICAL.
level = "INFO"
# Write logs to the console (colorized).
console = true
# Optional JSON-lines log file path (comment out to disable).
# file = "logs/weatherstar.jsonl"

```

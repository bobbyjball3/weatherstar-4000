# Themes

The WeatherStar 4000 engine is themed by name. A theme changes the look and
feel of every screen — colors, the fonts/backgrounds/logos/icons asset tree it
loads, and the product line shown in the screen header — without any per-screen
code branching on the theme. Themes are **data** (one TOML file per theme), so
adding or tweaking a look never requires writing Python.

## Choosing the active theme

The active theme is just a name:

```sh
uv run weatherstar4000 --sequence main --theme weatherstar3000
# or in config.toml
theme = "weatherstar3000"
```

Selection precedence: `--theme` > `WEATHERSTAR_THEME` > the top-level `theme`
key > `weatherstar4000` (the authentic WeatherStar 4000 look).

## Where theme files live

Each theme is a `*.theme.toml` file whose **file stem is the theme name**
(e.g. `weatherstar3000.theme.toml` → `weatherstar3000`). They are discovered
from these directories, highest precedence first:

1. `--themes-dir` / `WEATHERSTAR_THEMES_DIR`
2. `~/.config/weatherstar4000/themes/` (XDG user themes)
3. the built-in themes shipped inside the package (`builtin_themes/`)

Earlier directories shadow later ones by name, so a user theme can override a
built-in (or any other theme) of the same name. Malformed theme files are
skipped with a warning rather than aborting the run.

Built-in themes: `weatherstar4000` (default/base), `dark`, `high_contrast`,
`retro_green`, `amber`, and `weatherstar3000`.

## File format

```toml
# <name>.theme.toml  (file stem = theme name)
title = "WeatherStar 3000"     # product name (progress/loading text)
title_bottom = "3000"          # header bottom line; blank if unset
asset_dir = "static_assets_ws3000"  # media tree (default "static_assets")

[colors]
# Palette keys layered over the engine's small built-in base palette
# (white, yellow, blue, cyan, red). Colors are "#RRGGBB" hex or [r, g, b].
yellow = "#FFFFFF"
white = "#FFFFFF"
black = "#000000"
blue_gradient_1 = "#09246F"
blue_gradient_2 = "#364AC0"
cyan = "#8FFDFA"
red = "#FF4D4D"

[fonts]                 # optional: point the named font slots at your own files
title = ["ws3000.ttf", 32]
large = ["ws3000.ttf", 32]
normal = ["ws3000.ttf", 20]
```

### `colors`

Renderers read semantic keys (`white`, `yellow`, `blue`, `cyan`, `red`,
`blue_gradient_1`/`blue_gradient_2`, `purple_header`, `up`, `down`, ...).
`AppContext.colors` layers a theme's palette over a small in-code `BASE_COLORS`
(the keys screens read directly), so a theme file may be **partial** — any key
it omits falls back to the base value. Only define what your look overrides.

### `asset_dir`

When set, the media plugins (`fonts`, `backgrounds`, `logos`, `icons`) load from
`<asset_dir>/fonts_ttf/`, `<asset_dir>/backgrounds/`, etc. instead of the repo's
`static_assets/`. This is how a theme supplies its own typeface, background art,
logos and icons with no code changes.

A theme's asset tree applies **per media kind**: the engine only switches a media
plugin to the theme's directory when that subdirectory actually exists there.
A theme that ships `icons/` but no `backgrounds/` themes icons while keeping the
classic backgrounds; a theme with no asset tree at all (a recolor-only theme)
keeps the classic icons, fonts, backgrounds and logos. Precedence for a given
media kind: an explicit `[media.X] asset_dir` in the main config wins over the
theme; otherwise the theme's directory is used when it provides the subdirectory,
falling back to the built-in `static_assets` when it does not. So icons and fonts
never vanish under a theme that merely recolors the palette.

### `fonts`

Optional map of the named font slots (`title`, `large`, `extended`, `small`,
`normal`, `forecast`, `tiny`, `scroller`) to `[file, size]`. A theme that
points these at its own TTF files (e.g. the WeatherStar 3000 typeface) uses them
when present; otherwise the classic filenames are used.

## Adding your own theme

1. Drop a `<name>.theme.toml` into `~/.config/weatherstar4000/themes/`
   (or point `--themes-dir` at a directory of your own).
2. Set `theme = "<name>"` in `config.toml` (or pass `--theme <name>`).

You can shadow/extend any built-in by naming your file after it. There is no
central registry to update — discovery is purely file-based.

"""Tests for the theming system: TOML parsing, discovery, and engine wiring."""

from weatherstar.config_file import AppConfig
from weatherstar.engine import Builder, select_theme_name
from weatherstar.themes import (
    DEFAULT_THEME_NAME,
    ENV_THEME,
    FALLBACK_THEME,
    LayoutVariant,
    available_themes,
    builtin_themes_dir,
    coerce_variant,
    get_theme,
)


def _write_theme(directory, name, body):
    path = directory / f"{name}.theme.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parses_hex_and_rgb_colors_and_fonts(tmp_path):
    body = """
    title = "Testy"
    title_bottom = "42"
    asset_dir = "some_assets"
    [colors]
    yellow = "#A1B2C3"
    cyan = [0, 200, 150]
    [fonts]
    title = ["ws3000.ttf", 32]
    """
    _write_theme(tmp_path, "mytest", body)
    theme = get_theme("mytest", dirs=[tmp_path])
    assert theme.title == "Testy"
    assert theme.title_bottom == "42"
    assert theme.asset_dir == "some_assets"
    assert theme.colors["yellow"] == (0xA1, 0xB2, 0xC3)
    assert theme.colors["cyan"] == (0, 200, 150)
    assert theme.fonts["title"] == ("ws3000.ttf", 32)


def test_title_bottom_defaults_blank(tmp_path):
    _write_theme(tmp_path, "minimal", 'title = "Minimal"\n[colors]\nwhite = "#FFFFFF"')
    theme = get_theme("minimal", dirs=[tmp_path])
    assert theme.title_bottom == ""
    assert theme.asset_dir == "static_assets/weatherstar_4000"
    # Layout-family fields default to the Weather Star 4000 variant.
    assert theme.variant is LayoutVariant.WS4000
    assert theme.bottom_band is LayoutVariant.WS4000


def test_parses_variant_and_bottom_band(tmp_path):
    body = 'title = "3k"\nvariant = "3000"\nbottom_band = "3000"\n'
    _write_theme(tmp_path, "threek", body)
    theme = get_theme("threek", dirs=[tmp_path])
    assert theme.variant is LayoutVariant.WS3000
    assert theme.bottom_band is LayoutVariant.WS3000


def test_unknown_variant_falls_back_to_4000(tmp_path):
    _write_theme(tmp_path, "bogus", 'title = "Bogus"\nvariant = "300"\n')
    theme = get_theme("bogus", dirs=[tmp_path])
    assert theme.variant is LayoutVariant.WS4000
    assert theme.bottom_band is LayoutVariant.WS4000


def test_coerce_variant_handles_members_none_and_unknown():
    assert coerce_variant(LayoutVariant.WS3000) is LayoutVariant.WS3000
    assert coerce_variant("3000") is LayoutVariant.WS3000
    # Missing/blank values fall back silently (no warn); unknown values too.
    assert coerce_variant(None) is LayoutVariant.WS4000
    assert coerce_variant("") is LayoutVariant.WS4000
    assert coerce_variant("future") is LayoutVariant.WS4000
    assert coerce_variant("3000", fallback=LayoutVariant.WS3000) is LayoutVariant.WS3000


def test_invalid_file_is_skipped(tmp_path):
    _write_theme(tmp_path, "broken", '[colors]\nyellow = "not-a-color"')
    assert "broken" not in available_themes(dirs=[tmp_path])
    assert get_theme("broken", dirs=[tmp_path]) is FALLBACK_THEME


def test_unknown_theme_returns_fallback(tmp_path):
    assert get_theme("nope", dirs=[tmp_path]) is FALLBACK_THEME


# ---------------------------------------------------------------------------
# Discovery / precedence
# ---------------------------------------------------------------------------


def test_builtin_themes_are_discoverable():
    names = available_themes(dirs=[builtin_themes_dir()])
    for expected in ("weatherstar4000", "dark", "weatherstar3000", "amber"):
        assert expected in names
    theme = get_theme("weatherstar4000", dirs=[builtin_themes_dir()])
    assert theme.title == "Weather Star 4000"
    assert theme.title_bottom == "4000"


def test_higher_precedence_dir_shadows_lower(tmp_path):
    _write_theme(
        tmp_path,
        "weatherstar4000",
        'title = "Weather Star 4000"\ntitle_bottom = "4000"\n[colors]\nyellow = "#112233"\n',
    )
    dirs = [tmp_path, builtin_themes_dir()]
    assert get_theme("weatherstar4000", dirs=dirs).colors["yellow"] == (0x11, 0x22, 0x33)
    # A built-in not shadowed by the user dir still resolves.
    assert get_theme("dark", dirs=dirs).name == "dark"


def test_reversed_dir_order_keeps_builtin_first(tmp_path):
    _write_theme(
        tmp_path,
        "weatherstar4000",
        'title = "Weather Star 4000"\ntitle_bottom = "4000"\n[colors]\nyellow = "#112233"\n',
    )
    assert get_theme("weatherstar4000", dirs=[builtin_themes_dir(), tmp_path]).colors["yellow"] == (
        255,
        255,
        0,
    )


# ---------------------------------------------------------------------------
# Active-theme selection
# ---------------------------------------------------------------------------


def _appcfg(**data):
    return AppConfig({"sequence": "main", **data})


def test_select_theme_defaults_to_weatherstar4000(monkeypatch):
    monkeypatch.delenv(ENV_THEME, raising=False)
    assert select_theme_name(_appcfg()) == DEFAULT_THEME_NAME


def test_select_theme_config_key(monkeypatch):
    monkeypatch.delenv(ENV_THEME, raising=False)
    assert select_theme_name(_appcfg(theme="amber")) == "amber"


def test_select_theme_env_beats_config(monkeypatch):
    monkeypatch.setenv(ENV_THEME, "dark")
    assert select_theme_name(_appcfg(theme="amber")) == "dark"


def test_select_theme_cli_beats_env(monkeypatch):
    monkeypatch.setenv(ENV_THEME, "dark")
    assert select_theme_name(_appcfg(theme="amber"), cli_theme="weatherstar3000") == (
        "weatherstar3000"
    )


# ---------------------------------------------------------------------------
# Engine wiring: theme asset_dir + media loading
# ---------------------------------------------------------------------------

CFG = """
sequence = "demo"
[location]
lat = 28.5383
lon = -81.3792
[sequences.demo]
pause = 0.05
slides = [{ screen = "progress" }]
"""


def _register_media_classes() -> None:
    """Guarantee the real fonts/backgrounds media plugins are registered.

    test_skeleton clears the process-wide registry during restore, so media
    plugins may be missing here even though ``Builder`` discovered them earlier.
    Registering the concrete classes keeps this file self-contained.
    """
    from weatherstar.media.backgrounds import Backgrounds
    from weatherstar.media.fonts import Fonts
    from weatherstar.media.icons import Icons
    from weatherstar.media.logos import Logos
    from weatherstar.media.music import Music
    from weatherstar.registry import registry

    registry.register("media", "backgrounds", Backgrounds)
    registry.register("media", "fonts", Fonts)
    registry.register("media", "icons", Icons)
    registry.register("media", "logos", Logos)
    registry.register("media", "music", Music)


def test_builder_media_loads_from_theme_asset_dir(tmp_path, pygame_env):
    import pygame

    _register_media_classes()

    assets_dir = tmp_path / "ws3000_assets"
    (assets_dir / "backgrounds").mkdir(parents=True)
    stamp = pygame.Surface((16, 16))
    stamp.fill((200, 30, 200))
    pygame.image.save(stamp, str(assets_dir / "backgrounds" / "1.png"))

    themes_dir = tmp_path / "themes"
    _write_theme(
        themes_dir,
        "weatherstar3000",
        f'title = "Weather Star 3000"\ntitle_bottom = "3000"\nasset_dir = "{assets_dir}"\n',
    )

    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(CFG)
    appcfg = AppConfig.from_file(cfg_path)
    builder = Builder(appcfg, cli_theme="weatherstar3000", themes_dir=str(themes_dir))

    from weatherstar.engine import resolve_location

    surface = pygame.Surface((640, 480))
    deps = {"datasource": set(), "media": {"fonts", "backgrounds"}, "component": set()}
    ctx = builder.build_context(surface, location=resolve_location(appcfg), deps=deps)

    assert ctx.theme.name == "weatherstar3000"
    assert ctx.theme.title_bottom == "3000"
    assert ctx.theme.asset_dir == str(assets_dir)
    # The backgrounds media loaded from the *theme's* asset tree, not the repo default.
    backgrounds = ctx.assets.get("backgrounds") or {}
    assert "1" in backgrounds
    assert backgrounds["1"].get_at((0, 0))[:3] == (200, 30, 200)


def test_media_asset_dir_precedence(tmp_path, pygame_env):
    """An explicit, non-default [media.*] asset_dir beats the theme's dir."""
    _register_media_classes()

    from weatherstar.engine import Builder

    themes_dir = tmp_path / "themes"
    theme_assets = tmp_path / "theme_assets"
    _write_theme(
        themes_dir,
        "weatherstar3000",
        f'title = "Weather Star 3000"\ntitle_bottom = "3000"\nasset_dir = "{theme_assets}"\n',
    )
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(CFG)
    appcfg = AppConfig.from_file(cfg_path)
    builder = Builder(appcfg, cli_theme="weatherstar3000", themes_dir=str(themes_dir))

    # Theme provides nothing yet -> media stays on the default asset dir.
    assert (
        builder.make_media("backgrounds", str(theme_assets)).asset_dir
        == "static_assets/weatherstar_4000"
    )

    # Theme gains a backgrounds/ subdir -> themed backgrounds are used (whether
    # the scope omits asset_dir or merely repeats the built-in default).
    (theme_assets / "backgrounds").mkdir(parents=True)
    assert builder.make_media("backgrounds", str(theme_assets)).asset_dir == str(theme_assets)
    cfg2 = AppConfig(
        {**appcfg.data, "media": {"backgrounds": {"asset_dir": "static_assets/weatherstar_4000"}}}
    )
    assert Builder(cfg2, cli_theme="weatherstar3000", themes_dir=str(themes_dir)).make_media(
        "backgrounds", str(theme_assets)
    ).asset_dir == str(theme_assets)

    # A custom [media.backgrounds] asset_dir wins over the theme even when the
    # theme provides that media kind.
    cfg3 = AppConfig({**appcfg.data, "media": {"backgrounds": {"asset_dir": "custom_assets"}}})
    assert (
        Builder(cfg3, cli_theme="weatherstar3000", themes_dir=str(themes_dir))
        .make_media("backgrounds", str(theme_assets))
        .asset_dir
        == "custom_assets"
    )

    # A theme with an icons/ dir but no backgrounds/ dir themes icons only.
    icons_theme = tmp_path / "icons_theme"
    (icons_theme / "icons").mkdir(parents=True)
    assert builder.make_media("icons", str(icons_theme)).asset_dir == str(icons_theme)
    assert (
        builder.make_media("backgrounds", str(icons_theme)).asset_dir
        == "static_assets/weatherstar_4000"
    )

    # Conversely, a theme that only recolors (no asset tree) must not silence
    # the classic icons/fonts/logos.
    assert (
        builder.make_media("icons", str(theme_assets)).asset_dir == "static_assets/weatherstar_4000"
    )
    assert (
        builder.make_media("logos", str(theme_assets)).asset_dir == "static_assets/weatherstar_4000"
    )
    assert (
        builder.make_media("fonts", str(theme_assets)).asset_dir == "static_assets/weatherstar_4000"
    )

    # Music is not visual: it never follows the theme's asset dir.
    assert (
        builder.make_media("music", str(theme_assets)).asset_dir == "static_assets/weatherstar_4000"
    )

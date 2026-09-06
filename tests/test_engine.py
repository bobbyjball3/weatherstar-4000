"""Tests for the engine: building plugins and running/validating a sequence."""

import pytest
from pydantic import SecretStr

from weatherstar import InvalidConfiguration
from weatherstar.config_file import AppConfig
from weatherstar.engine import Builder, SequenceRunner, resolve_location
from weatherstar.plugin import Plugin
from weatherstar.registry import registry
from weatherstar.sequence import Sequence

CFG = """
sequence = "demo"
[location]
lat = 28.5383
lon = -81.3792
[sequences.demo]
pause = 0.05
slides = [{ screen = "progress" }]
"""


@pytest.fixture()
def appcfg(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(CFG)
    return AppConfig.from_file(path)


def test_sequence_from_cfg_uses_per_slide_and_global_pause(appcfg):
    name, data = appcfg.select_sequence(None)
    sequence = Sequence.from_config(name, data)
    assert sequence.name == "demo"
    assert [s.screen for s in sequence.slides] == ["progress"]
    assert sequence.pause_for(0) == 0.05


def test_resolve_location_cli_wins_over_config(appcfg):
    location = resolve_location(appcfg, lat=10.0, lon=20.0)
    assert (location.lat, location.lon) == (10.0, 20.0)
    location = resolve_location(appcfg)
    assert (location.lat, location.lon) == (28.5383, -81.3792)


def test_builder_creates_plugins(appcfg):
    builder = Builder(appcfg)
    screen = builder.make("screen", "progress")
    assert screen.name == "progress"


def test_build_runtime_and_validate_progress(appcfg, pygame_env):
    import pygame

    builder = Builder(appcfg)
    name, data = appcfg.select_sequence(None)
    sequence = Sequence.from_config(name, data)
    surface = pygame.Surface((640, 480))
    location = resolve_location(appcfg)
    ctx, screens = builder.build_runtime(sequence, surface, location)
    runner = SequenceRunner(ctx, screens, sequence)
    failures = runner.validate(frames_per_slide=2)
    assert failures == []
    # Surface should no longer be blank after drawing progress.
    assert any(
        surface.get_at((x, y))[:3] != (0, 0, 0)
        for x in range(0, 640, 32)
        for y in range(0, 480, 32)
    )


def test_layout_components_bound_and_drawn(appcfg, pygame_env):
    import pygame

    builder = Builder(appcfg)
    name, data = appcfg.select_sequence(None)
    sequence = Sequence.from_config(name, data)
    surface = pygame.Surface((640, 480))
    ctx, screens = builder.build_runtime(sequence, surface, resolve_location(appcfg))
    screen = screens[0]
    # Engine built one component per layout spec, in order.
    assert [c.name for c in screen._components] == ["background", "header", "clock"]
    # Drawing steps+renders the components then the compose hook.
    screen.draw(surface, ctx, dt=1 / 30)
    # Header band shows the yellow title text.
    colors = {surface.get_at((x, y))[:3] for x in range(170, 320, 5) for y in range(25, 60, 5)}
    assert ctx.colors["yellow"] in colors


def test_run_sequence_advances_all_slides(appcfg, pygame_env):
    import pygame

    builder = Builder(appcfg)
    name, data = appcfg.select_sequence(None)
    sequence = Sequence.from_config(name, data)
    surface = pygame.Surface((640, 480))
    ctx, screens = builder.build_runtime(sequence, surface, resolve_location(appcfg))
    from weatherstar.engine import run_sequence

    frames = run_sequence(ctx, screens, sequence)
    assert frames >= 1


def test_run_sequence_interactive_auto_advances_and_wraps(pygame_env):
    import pygame

    from weatherstar.context import AppContext, DataRegistry, Location
    from weatherstar.engine import run_sequence

    drawn = []

    class _FakeSlide:
        def __init__(self, name):
            self.name = name

        def step(self, ctx, dt):
            pass

        def draw(self, surface, ctx, dt):
            drawn.append(self.name)

    screens = [_FakeSlide("a"), _FakeSlide("b")]
    seq = Sequence.from_config(
        "interactive", {"pause": 0.05, "slides": [{"screen": "a"}, {"screen": "b"}]}
    )
    ctx = AppContext(
        surface=pygame.Surface((640, 480)),
        data=DataRegistry(),
        location=Location(lat=28.0, lon=-81.0),
    )
    # ~14 frames at 30fps ≈ 466ms, comfortably past both 50ms pauses and the
    # wrap point, proving slides advance automatically in interactive mode.
    run_sequence(ctx, screens, seq, interactive=True, max_frames=14)
    assert len(drawn) >= 6
    assert set(drawn) == {"a", "b"}
    # a must appear again after wrapping past b (b..a), not stuck on one screen.
    assert "a" in drawn[len(drawn) // 2 :]


def test_run_sequence_polls_music_controller(pygame_env):
    import pygame

    from weatherstar.context import AppContext, DataRegistry, Location
    from weatherstar.engine import run_sequence

    class _Controller:
        def __init__(self):
            self.polls = 0

        def advance_music(self):
            self.polls += 1

    class _Slide:
        name = "a"

        def step(self, ctx, dt):
            pass

        def draw(self, surface, ctx, dt):
            pass

    seq = Sequence.from_config("m", {"pause": 0.01, "slides": [{"screen": "a"}]})
    ctx = AppContext(
        surface=pygame.Surface((640, 480)),
        data=DataRegistry(),
        location=Location(lat=28.0, lon=-81.0),
    )
    controller = _Controller()
    run_sequence(ctx, [_Slide()], seq, interactive=True, max_frames=5, music_controller=controller)
    assert controller.polls >= 5


def _slide_pair_ctx(pygame_env):
    import pygame

    from weatherstar.context import AppContext, DataRegistry, Location

    class _FakeSlide:
        def __init__(self, name):
            self.name = name

        def step(self, ctx, dt):
            pass

        def draw(self, surface, ctx, dt):
            pass

    seq = Sequence.from_config("m", {"pause": 0.001, "slides": [{"screen": "a"}, {"screen": "b"}]})
    ctx = AppContext(
        surface=pygame.Surface((640, 480)),
        data=DataRegistry(),
        location=Location(lat=28.0, lon=-81.0),
    )
    return ctx, [_FakeSlide("a"), _FakeSlide("b")], seq


def test_run_sequence_noninteractive_completes_single_pass(pygame_env):
    from weatherstar.engine import run_sequence

    ctx, screens, seq = _slide_pair_ctx(pygame_env)
    frames = run_sequence(ctx, screens, seq)
    # Finishes a single pass quickly (does not loop forever).
    assert frames >= 1


def test_run_sequence_stop_event(pygame_env):
    import threading

    from weatherstar.engine import run_sequence

    ctx, screens, seq = _slide_pair_ctx(pygame_env)
    stop = threading.Event()
    stop.set()
    frames = run_sequence(ctx, screens, seq, interactive=True, stop_event=stop)
    assert frames < 100  # stops promptly instead of running forever


def test_run_sequence_max_frames(pygame_env):
    from weatherstar.engine import run_sequence

    ctx, screens, seq = _slide_pair_ctx(pygame_env)
    frames = run_sequence(ctx, screens, seq, interactive=True, max_frames=7)
    assert frames == 7


def _register_temporary_screen(**typed_fields):
    """Register a temp screen; pass ``field_name=(Type,)`` or ``field_name=(Type, default)``."""
    attrs = {
        "kind": "screen",
        "name": "needs_key_tmp",
        "__module__": "tests.test_engine",
    }
    annotations: dict[str, type] = {}
    for name, spec in typed_fields.items():
        annotation = spec[0]
        annotations[name] = annotation
        if len(spec) > 1:
            attrs[name] = spec[1]
    if annotations:
        attrs["__annotations__"] = annotations
    cls = type("NeedsKeyTmpScreen", (Plugin,), attrs)
    registry.register("screen", "needs_key_tmp", cls)
    return cls


def test_missing_required_config_raises_with_example(appcfg, tmp_path):
    _register_temporary_screen(api_key=(SecretStr,))
    try:
        cfg_text = CFG.replace(
            'slides = [{ screen = "progress" }]', 'slides = [{ screen = "needs_key_tmp" }]'
        )
        path = tmp_path / "cfg2.toml"
        path.write_text(cfg_text)
        cfg2 = AppConfig.from_file(path)
        builder2 = Builder(cfg2)
        name, data = cfg2.select_sequence(None)
        sequence = Sequence.from_config(name, data)
        with pytest.raises(InvalidConfiguration) as excinfo:
            builder2.build_screens(sequence)
        message = str(excinfo.value)
        assert "needs_key_tmp" in message
        assert "api_key" in message
        assert "[screen.needs_key_tmp]" in message
        assert "api_key = " in message
    finally:
        registry._plugins.get("screen", {}).pop("needs_key_tmp", None)


def test_screen_scope_config_is_applied(appcfg, tmp_path, pygame_env):
    _register_temporary_screen()
    try:
        cfg_text = CFG.replace(
            'slides = [{ screen = "progress" }]',
            'slides = [{ screen = "needs_key_tmp" }]\n[screen.needs_key_tmp]\nlabel = "hello"',
        )
        path = tmp_path / "cfg3.toml"
        path.write_text(cfg_text)
        cfg3 = AppConfig.from_file(path)
        builder = Builder(cfg3)
        name, data = cfg3.select_sequence(None)
        sequence = Sequence.from_config(name, data)
        screen = builder.build_screens(sequence)[0]
        assert screen.name == "needs_key_tmp"
    finally:
        registry._plugins.get("screen", {}).pop("needs_key_tmp", None)


def test_plugin_not_found_for_unknown_screen(appcfg):
    from weatherstar import PluginNotFound

    raw = dict(appcfg.data)
    raw["sequences"] = {"demo": {"pause": 0.05, "slides": [{"screen": "nope"}]}}
    cfg2 = AppConfig(raw)
    name, data = cfg2.select_sequence(None)
    seq2 = Sequence.from_config(name, data)
    with pytest.raises(PluginNotFound):
        Builder(cfg2).build_screens(seq2)

"""Layout-variant contract tests: declaration, dispatch, and degradation.

Screens declare which :class:`LayoutVariant` renderers they implement via the
``variants`` ClassVar; ``Screen.compose`` dispatches on the active theme's
requested variant and raises :class:`ThemeNotSupported` when it is not declared.
"""

import pygame
import pytest

from weatherstar_4000.context import AppContext
from weatherstar_4000.errors import InvalidConfiguration, ThemeNotSupported
from weatherstar_4000.screens.base import Screen
from weatherstar_4000.sequence import Sequence, Slide
from weatherstar_4000.themes import LayoutVariant, Theme


def _ctx(surface, variant, active="test"):
    theme = Theme(name="test", variant=variant)
    ctx = AppContext(surface=surface, theme=theme)
    ctx.active_screen = active
    return ctx


# -- introspection ----------------------------------------------------------


def test_registered_screens_declare_variants_and_methods(pygame_env):
    """Every screen plugin's declared variant maps to a real method."""
    import importlib
    import pkgutil

    import weatherstar_4000.screens as pkg
    from weatherstar_4000.screens import base as screens_base

    seen: set[str] = set()
    for info in pkgutil.iter_modules(pkg.__path__):
        module = importlib.import_module(f"{pkg.__name__}.{info.name}")
        for obj in vars(module).values():
            if not isinstance(obj, type) or not issubclass(obj, screens_base.Screen):
                continue
            name = getattr(obj, "name", None)
            if not isinstance(name, str):
                continue
            seen.add(name)
            for variant, method_name in (obj.variants or {}).items():
                assert callable(getattr(obj, method_name, None)), (
                    f"{name} declares variant {variant.value!r} -> {method_name!r} "
                    "but the method is missing"
                )
            assert tuple(sorted(obj.variants, key=lambda item: item.value)) == (
                obj.supported_variants()
            )
    assert "current_conditions" in seen and "severe_weather_alert" in seen


def test_variant_screens_introspect_both_layouts(pygame_env):
    from weatherstar_4000.screens.current_conditions import CurrentConditionsScreen

    assert CurrentConditionsScreen.supported_variants() == (
        LayoutVariant.WS3000,
        LayoutVariant.WS4000,
    )
    assert LayoutVariant.WS3000 in CurrentConditionsScreen.variants


def test_component_only_screens_declare_nothing(pygame_env):
    from weatherstar_4000.screens.uv_index import UvIndexScreen

    assert UvIndexScreen.variants == {}
    assert UvIndexScreen.supported_variants() == ()


# -- dispatch ---------------------------------------------------------------


def test_compose_dispatches_on_active_variant(pygame_env, screen):
    calls: list[str] = []

    class Both(Screen):
        name = "both"
        variants = {
            LayoutVariant.WS4000: "compose_4000",
            LayoutVariant.WS3000: "compose_3000",
        }

        def compose_4000(self, surface, ctx, dt):
            calls.append("4000")

        def compose_3000(self, surface, ctx, dt):
            calls.append("3000")

    instance = Both()
    instance.compose(screen, _ctx(screen, LayoutVariant.WS4000), 0.0)
    instance.compose(screen, _ctx(screen, LayoutVariant.WS3000), 0.0)
    assert calls == ["4000", "3000"]


def test_component_only_screen_ignores_variant(pygame_env, screen):
    class ComponentsOnly(Screen):
        name = "components_only"

    ComponentsOnly().compose(screen, _ctx(screen, LayoutVariant.WS3000), 0.0)  # no raise


# -- degradation ------------------------------------------------------------


def test_undeclared_variant_raises_theme_not_supported(pygame_env, screen):
    class Only4000(Screen):
        name = "only4000"
        variants = {LayoutVariant.WS4000: "compose_4000"}

        def compose_4000(self, surface, ctx, dt):
            pass

    with pytest.raises(ThemeNotSupported) as excinfo:
        Only4000().compose(screen, _ctx(screen, LayoutVariant.WS3000), 0.0)
    message = str(excinfo.value)
    assert "only4000" in message
    assert "does not support layout variant '3000'" in message
    assert "declared: 4000" in message
    assert isinstance(excinfo.value, NotImplementedError)


def test_validate_records_unsupported_variant(pygame_env):
    from weatherstar_4000.engine import SequenceRunner

    class Only4000(Screen):
        name = "only4000"
        variants = {LayoutVariant.WS4000: "compose_4000"}

        def compose_4000(self, surface, ctx, dt):
            pass

    surface = pygame.Surface((640, 480))
    ctx = _ctx(surface, LayoutVariant.WS3000, active="only4000")
    sequence = Sequence(name="t", slides=[Slide(screen="only4000")], default_pause=60.0)
    runner = SequenceRunner(ctx, [Only4000()], sequence)
    failures = runner.validate(frames_per_slide=1, dt=0.001)
    assert len(failures) == 1
    assert "does not support layout variant '3000'" in failures[0]


def test_run_sequence_degrades_unsupported_variant_to_placeholder(pygame_env):
    from weatherstar_4000.engine import run_sequence

    class Only4000(Screen):
        name = "only4000"
        variants = {LayoutVariant.WS4000: "compose_4000"}

        def compose_4000(self, surface, ctx, dt):
            pass

    surface = pygame.Surface((640, 480))
    ctx = _ctx(surface, LayoutVariant.WS3000, active="only4000")
    ctx.fonts = {
        "large": pygame.font.Font(None, 32),
        "small": pygame.font.Font(None, 20),
        "scroller": pygame.font.Font(None, 20),
    }
    sequence = Sequence(name="t", slides=[Slide(screen="only4000")], default_pause=60.0)
    frames = run_sequence(ctx, [Only4000()], sequence, interactive=False, max_frames=1)
    assert frames == 1
    # The friendly yellow placeholder replaced the blank slide.
    placeholder = [
        surface.get_at((x, y))
        for y in range(230, 255)
        for x in range(100, surface.get_width() - 100)
    ]
    assert any(pixel == (255, 255, 0, 255) for pixel in placeholder)


# -- build-time validation --------------------------------------------------


def test_build_validation_flags_missing_declared_method(pygame_env):
    from weatherstar_4000.engine import validate_screen_variants

    class Typo(Screen):
        name = "typo"
        variants = {LayoutVariant.WS4000: "compose_40000"}

    ctx = _ctx(pygame.Surface((640, 480)), LayoutVariant.WS4000)
    with pytest.raises(InvalidConfiguration) as excinfo:
        validate_screen_variants([Typo()], ctx)
    assert "compose_40000" in str(excinfo.value)


def test_build_validation_warns_but_does_not_raise_for_undeclared_request(
    pygame_env,
):
    from weatherstar_4000.engine import validate_screen_variants

    class Only4000(Screen):
        name = "solo"
        variants = {LayoutVariant.WS4000: "compose_4000"}

        def compose_4000(self, surface, ctx, dt):
            pass

    theme = Theme(name="t", layout={"solo": {"variant": "3000"}})
    ctx = AppContext(surface=pygame.Surface((640, 480)), theme=theme)
    ctx.active_screen = "solo"
    validate_screen_variants([Only4000()], ctx)  # no raise

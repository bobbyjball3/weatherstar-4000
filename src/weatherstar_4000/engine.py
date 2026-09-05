"""Engine: build plugins from config, then run or validate a Sequence.

Responsibilities:
- resolve the Sequence (CLI > envvar > config),
- instantiate every referenced Screen and its composed Datasource/Media/
  Component plugins, binding config scopes (raising InvalidConfiguration when a
  required scope is missing),
- run the pygame loop with per-slide pauses, or render a validation pass.

The engine is pygame-optional at import time; pygame is only imported inside
methods that need it.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from weatherstar_4000.config_file import AppConfig
from weatherstar_4000.context import AppContext, DataRegistry, Location
from weatherstar_4000.errors import ConfigError
from weatherstar_4000.logging_setup import get_logger
from weatherstar_4000.registry import discover, registry
from weatherstar_4000.sequence import Sequence

DEFAULT_PAUSE = 15.0
#: Media plugins auto-loaded into every context when they are registered.
_BASE_MEDIA = ("fonts",)


def resolve_location(
    appcfg: AppConfig, lat: float | None = None, lon: float | None = None
) -> Location:
    """Resolve coordinates from CLI args > [location] config section.

    Raises ConfigError when no usable coordinates can be found.
    """
    if lat is not None and lon is not None:
        return Location(lat=lat, lon=lon)
    loc = appcfg.location_options()
    if loc["lat"] is not None and loc["lon"] is not None:
        return Location(
            lat=float(loc["lat"]),
            lon=float(loc["lon"]),
            description=loc["description"] or "",
        )
    raise ConfigError(
        "No location configured. Pass --lat/--lon or add a [location] section "
        "with `lat` and `lon` to the config file."
    )


def select_theme_name(appcfg: AppConfig) -> str:
    return str(appcfg.data.get("theme", "classic"))


def music_enabled(appcfg: AppConfig) -> bool:
    """Whether ambient background music is requested via ``[media.music]``."""
    return bool(appcfg.scope("media", "music").get("enabled"))


class Builder:
    """Constructs datasources/media/components/screens for a sequence."""

    def __init__(self, appcfg: AppConfig):
        self.appcfg = appcfg
        self.log = get_logger("weatherstar4000.engine")
        self._music_player = None
        discover()

    # -- per-plugin instantiation -------------------------------------------

    def make(self, kind: str, name: str) -> Any:
        cls = registry.get(kind, name)
        return cls.from_config(self.appcfg.scope(kind, name))

    def build_data(self, names: Iterable[str]) -> DataRegistry:
        data = DataRegistry()
        for name in sorted(names):
            data.register(name, self.make("datasource", name))
        return data

    def build_media(self, names: Iterable[str], ctx: AppContext) -> None:
        for name in sorted(names):
            media = self.make("media", name)
            media.load(ctx)

    def build_components(self, names: Iterable[str], ctx: AppContext) -> dict[str, Any]:
        built: dict[str, Any] = {}
        for name in sorted(names):
            component = self.make("component", name)
            component.prepare(ctx)
            built[name] = component
        return built

    def build_screens(self, sequence: Sequence) -> list[Any]:
        return [self.make("screen", name) for name in sequence.screen_names()]

    # -- dependency graph -----------------------------------------------------

    def sequence_dependencies(self, sequence: Sequence) -> dict[str, set[str]]:
        kinds = {"datasource": set(), "media": set(), "component": set()}
        for name in sequence.screen_names():
            cls = registry.get("screen", name)
            kinds["datasource"].update(cls.datasources or ())
            kinds["media"].update(cls.media or ())
            kinds["component"].update(cls.components or ())
        # Auto include registered base media that every screen may rely on.
        available = set(registry.names("media"))
        kinds["media"].update(n for n in _BASE_MEDIA if n in available)
        # Music is ambient/config-driven, not a screen dependency: include it
        # whenever [media.music] enabled = true.
        if music_enabled(self.appcfg) and "music" in available:
            kinds["media"].add("music")
        return kinds

    def build_context(
        self,
        surface: Any,
        *,
        location: Location,
        deps: dict[str, set[str]] | None = None,
    ) -> AppContext:
        """Build a fully-populated AppContext for a set of plugin dependencies."""
        from weatherstar_4000.themes import get_theme

        ctx = AppContext(
            surface=surface,
            theme=get_theme(select_theme_name(self.appcfg)),
            location=location,
        )
        media_names = set(deps["media"]) if deps else set()
        self.build_media(media_names, ctx)
        ctx.icon_manager = ctx.assets.get("icon_manager")
        if deps:
            ctx.data = self.build_data(deps["datasource"])
        return ctx

    def build_runtime(
        self, sequence: Sequence, surface: Any, location: Location
    ) -> tuple[AppContext, list[Any]]:
        deps = self.sequence_dependencies(sequence)
        ctx = self.build_context(surface, location=location, deps=deps)
        components = self.build_components(deps["component"], ctx)
        ctx.assets["components"] = components
        screens = self.build_screens(sequence)
        for screen in screens:
            screen.prepare(ctx)
        return ctx, screens

    def start_music(self, ctx: AppContext) -> bool:
        """Start ambient background music if configured; returns True if playing."""
        if not music_enabled(self.appcfg) or "music" not in registry.names("media"):
            self._music_player = None
            return False
        music = self.make("media", "music")
        started = music.play(ctx)
        self._music_player = music if started else None
        return started

    def advance_music(self) -> None:
        """Advance to the next shuffled track when the current one ends."""
        if self._music_player is not None:
            self._music_player.advance()

    @staticmethod
    def stop_music() -> None:
        from weatherstar_4000.media.music import Music

        Music.stop()


class SequenceRunner:
    """Drives a built sequence on a pygame surface."""

    def __init__(self, ctx: AppContext, screens: list[Any], sequence: Sequence):
        self.ctx = ctx
        self.screens = screens
        self.sequence = sequence
        self.by_name = {screen.name: screen for screen in screens}
        self.log = get_logger("weatherstar4000.engine")

    def step(self, index: int, dt: float) -> None:
        name = self.sequence.slides[index].screen
        screen = self.by_name[name]
        screen.step(self.ctx, dt)
        screen.draw(self.ctx.surface, self.ctx, dt)

    def validate(self, frames_per_slide: int = 1, dt: float = 1 / 30) -> list[str]:
        """Render each slide headlessly; return per-slide failures (empty = pass)."""
        failures: list[str] = []
        for index, slide in enumerate(self.sequence.slides):
            for frame in range(frames_per_slide):
                try:
                    self.step(index, dt)
                except Exception as exc:  # noqa: BLE001 - report per slide
                    failures.append(f"{slide.screen} (frame {frame}): {exc!r}")
                    break
        return failures


def run_sequence(
    ctx: AppContext,
    screens: list[Any],
    sequence: Sequence,
    *,
    fps: int = 30,
    interactive: bool = False,
    max_frames: int | None = None,
    stop_event: Any = None,
    music_controller: Any = None,
) -> int:
    """Execute a sequence, returning the number of frames drawn.

    Non-interactive: slides auto-advance by their pause duration and a single
    full pass is drawn.  Interactive: a pygame event loop until QUIT/ESC.
    When a ``music_controller`` (e.g. an engine ``Builder``) is supplied its
    ``advance_music()`` is polled each frame so the playlist keeps moving.
    """
    import pygame

    from weatherstar_4000.ticker import BottomTicker

    runner = SequenceRunner(ctx, screens, sequence)
    ticker = BottomTicker()
    clock = pygame.time.Clock()
    slide_index = 0
    slide_elapsed = 0.0
    frames = 0
    running = True

    while running:
        dt_ms = clock.tick(fps)
        dt = dt_ms / 1000.0
        frames += 1

        if interactive:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        delta = -1 if event.key == pygame.K_LEFT else 1
                        slide_index = (slide_index + delta) % len(sequence.slides)
                        slide_elapsed = 0.0

        # Auto-advance by the per-slide pause in both interactive and
        # non-interactive modes. Interactive runs wrap around forever;
        # non-interactive runs stop after a single pass.
        finished = False
        slide_elapsed += dt_ms
        pause_ms = int(sequence.pause_for(slide_index) * 1000)
        if pause_ms > 0:
            while slide_elapsed >= pause_ms:
                slide_elapsed -= pause_ms
                slide_index += 1
                if slide_index >= len(sequence.slides):
                    if interactive:
                        slide_index = 0
                        slide_elapsed = 0.0
                    else:
                        finished = True
                    break
                pause_ms = int(sequence.pause_for(slide_index) * 1000)
                if pause_ms <= 0:
                    break
        elif interactive or slide_index < len(sequence.slides) - 1:
            # A zero pause means "advance immediately", one slide per frame.
            slide_index = (slide_index + 1) % len(sequence.slides)
            slide_elapsed = 0.0
        else:
            finished = True

        if finished:
            running = False
            break

        runner.step(slide_index, dt)
        ticker.render(ctx.surface, ctx, dt)
        if music_controller is not None:
            advance = getattr(music_controller, "advance_music", None)
            if advance is not None:
                advance()
        if pygame.display.get_surface() is not None:
            pygame.display.flip()

        if max_frames is not None and frames >= max_frames:
            running = False
        if stop_event is not None and stop_event.is_set():
            running = False

    return frames

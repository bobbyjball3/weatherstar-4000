"""Command-line entrypoint for the Weather Star engine.

Usage::

    weatherstar [--config PATH] [--sequence NAME] [--lat F] [--lon F]
                   [--log-level LEVEL] [--log-file PATH] [--no-console]
                   [--validate] [--frames N]
    weatherstar generate-config [--sequence NAME] [-o PATH]

Sequence precedence is CLI flag > WEATHERSTAR_SEQUENCE envvar > config
``sequence`` key.  A config file (default ~/.config/weatherstar/config.toml,
overridable via ``--config`` / ``WEATHERSTAR_CONFIG``) is required unless
``--sequence`` plus coordinates are supplied.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from weatherstar import engine
from weatherstar.config_file import (
    ENV_SEQUENCE,
    AppConfig,
    LoggingConfig,
    VideoConfig,
    discover_config_path,
)
from weatherstar.errors import ConfigError, WeatherStarError
from weatherstar.registry import discover

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="weatherstar")
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate-config", help="Emit a skeleton TOML config")
    gen.add_argument("--sequence", default="main", help="Sequence name to template")
    gen.add_argument("-o", "--output", help="Write to PATH instead of stdout")

    parser.add_argument("--config", help="Path to config TOML (overrides env/default)")
    parser.add_argument("--sequence", help=f"Sequence name (overrides {ENV_SEQUENCE}/config)")
    parser.add_argument("--theme", help="Theme name (overrides WEATHERSTAR_THEME/config `theme`)")
    parser.add_argument("--themes-dir", help="Directory containing *.theme.toml theme files")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--log-level", default=None, choices=list(_LOG_LEVELS))
    parser.add_argument("--log-file", help="Also write structured JSON logs to PATH")
    parser.add_argument("--no-console", action="store_true", help="Disable stdout/stderr logs")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Headless: render each slide once and report failures",
    )
    parser.add_argument("--frames", type=int, default=None, help="Stop after N frames")
    return parser


def _load_app_config(path: Path | None) -> AppConfig:
    if path is None:
        raise ConfigError(
            "No config file found. Create one (see generate-config), or pass "
            "--config PATH. A config file is required unless explicit "
            "--sequence and location arguments are supplied."
        )
    return AppConfig.from_file(path)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        discover()
        if args.command == "generate-config":
            return _generate_config(args)
        return _run(args)
    except WeatherStarError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


def _generate_config(args: argparse.Namespace) -> int:
    from weatherstar import skeleton

    text = skeleton.render_skeleton(sequence_name=args.sequence)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    else:
        print(text)
    return 0


def _resolve_app_config(args: argparse.Namespace) -> AppConfig | None:
    path = discover_config_path(args.config)
    return _load_app_config(path) if path is not None else None


def _run(args: argparse.Namespace) -> int:
    import pygame

    from weatherstar.logging_setup import setup_logging
    from weatherstar.sequence import Sequence

    appcfg = _resolve_app_config(args)
    log_cfg = appcfg.logging if appcfg is not None else LoggingConfig()
    level_name = (args.log_level or log_cfg.level or "INFO").upper()
    console = not (args.no_console or log_cfg.console is False)
    log_file = args.log_file or log_cfg.file

    setup_logging(_LOG_LEVELS.get(level_name, logging.INFO), console=console, log_file=log_file)

    if appcfg is None:
        # No config file: require explicit sequence + location on the CLI.
        if not args.sequence or args.lat is None or args.lon is None:
            print(
                "error: a config file is required unless --sequence, --lat and --lon "
                "are all supplied.",
                file=sys.stderr,
            )
            return 2
        appcfg = AppConfig({"sequence": args.sequence})

    seq_name, seq_data = appcfg.select_sequence(args.sequence)
    sequence = Sequence.from_config(seq_name, seq_data)

    builder = engine.Builder(appcfg, cli_theme=args.theme, themes_dir=args.themes_dir)
    location = engine.resolve_location(appcfg, args.lat, args.lon)
    video = appcfg.video

    if args.validate:
        return _validate(builder, sequence, location, video)

    pygame.init()
    surface = pygame.display.set_mode((video.width, video.height))
    ctx, screens = builder.build_runtime(sequence, surface, location)
    pygame.display.set_caption(ctx.theme.title)
    builder.start_music(ctx)
    try:
        engine.run_sequence(
            ctx,
            screens,
            sequence,
            fps=video.fps,
            interactive=True,
            max_frames=args.frames,
            music_controller=builder,
        )
    finally:
        engine.Builder.stop_music()
    pygame.quit()
    return 0


def _validate(builder: engine.Builder, sequence, location, video: VideoConfig) -> int:
    import pygame

    pygame.init()
    surface = pygame.Surface((video.width, video.height))
    ctx, screens = builder.build_runtime(sequence, surface, location)
    failures = engine.SequenceRunner(ctx, screens, sequence).validate()
    pygame.quit()
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        print(f"error: {len(failures)} slide(s) failed to render", file=sys.stderr)
        return 1
    print(f"OK: {len(sequence.slides)} slide(s) rendered successfully")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

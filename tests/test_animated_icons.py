"""Tests for the animated weather icons module."""

import logging

import pygame
import pytest
from PIL import Image

from weatherstar_4000.animated_icons import AnimatedIcon, AnimatedIconManager


def _make_gif(path, frames=2, duration=100):
    imgs = []
    for i in range(frames):
        img = Image.new("RGBA", (10, 10), (255 - i * 40, 0, 0, 255))
        imgs.append(img)
    imgs[0].save(
        path, save_all=True, append_images=imgs[1:], duration=duration, loop=0, format="GIF"
    )


def _make_png(path):
    surface = pygame.Surface((10, 10))
    surface.fill((0, 255, 0))
    pygame.image.save(surface, str(path))


@pytest.fixture()
def icon_dir(tmp_path):
    _make_gif(tmp_path / "Clear.gif", frames=2, duration=100)
    _make_gif(tmp_path / "Single.gif", frames=1)
    _make_png(tmp_path / "Static.png")
    return tmp_path


# --- AnimatedIcon ----------------------------------------------------------


def test_loads_multi_frame_gif(icon_dir, display):
    # Act
    icon = AnimatedIcon(str(icon_dir / "Clear.gif"))

    # Assert
    assert len(icon.frames) == 2
    assert len(icon.durations) == 2
    assert icon.total_duration == pytest.approx(0.2)


def test_single_frame_gif_becomes_static(icon_dir, display):
    # Act
    icon = AnimatedIcon(str(icon_dir / "Single.gif"))

    # Assert
    assert icon.static_image is not None
    assert icon.frames == []


def test_get_current_frame_returns_static_when_present(icon_dir, display):
    # Arrange
    icon = AnimatedIcon(str(icon_dir / "Single.gif"))

    # Act
    frame = icon.get_current_frame()

    # Assert
    assert frame is icon.static_image


def test_get_current_frame_returns_none_when_no_frames(display):
    # Arrange
    icon = AnimatedIcon.__new__(AnimatedIcon)
    icon.static_image = None
    icon.frames = []
    icon.last_update = 0

    # Act
    frame = icon.get_current_frame()

    # Assert
    assert frame is None


def test_get_current_frame_first_frame_on_start(icon_dir, display):
    # Arrange
    icon = AnimatedIcon(str(icon_dir / "Clear.gif"))
    icon.last_update = 0

    # Act
    frame = icon.get_current_frame()

    # Assert
    assert frame is icon.frames[0]
    assert icon.last_update != 0


def test_get_current_frame_selects_by_elapsed(icon_dir, display, monkeypatch):
    # Arrange
    icon = AnimatedIcon(str(icon_dir / "Clear.gif"))
    icon.last_update = 100.0
    monkeypatch.setattr("time.time", lambda: 100.15)  # into second frame (0.1s duration)

    # Act
    frame = icon.get_current_frame()

    # Assert
    assert frame is icon.frames[1]


def test_get_current_frame_resets_when_past_total(icon_dir, display, monkeypatch):
    # Arrange
    icon = AnimatedIcon(str(icon_dir / "Clear.gif"))
    icon.last_update = 100.0
    monkeypatch.setattr("time.time", lambda: 200.0)  # way past 0.2s total

    # Act
    frame = icon.get_current_frame()

    # Assert
    assert frame is icon.frames[0]
    assert icon.last_update == 200.0


def test_get_scaled_frame(icon_dir, display):
    # Arrange
    icon = AnimatedIcon(str(icon_dir / "Clear.gif"))
    icon.last_update = 0

    # Act
    scaled = icon.get_scaled_frame(40, 40)

    # Assert
    assert scaled is not None
    assert scaled.get_size() == (40, 40)


def test_get_scaled_frame_none_when_missing(display):
    # Arrange
    icon = AnimatedIcon.__new__(AnimatedIcon)
    icon.frames = []
    icon.static_image = None

    # Act
    scaled = icon.get_scaled_frame(10, 10)

    # Assert
    assert scaled is None


def test_reset_animation(icon_dir, display):
    # Arrange
    icon = AnimatedIcon(str(icon_dir / "Clear.gif"))
    icon.current_frame = 1
    icon.last_update = 123

    # Act
    icon.reset_animation()

    # Assert
    assert icon.current_frame == 0
    assert icon.last_update == 0


def test_fallback_to_static_when_pil_unavailable(icon_dir, display, monkeypatch, caplog):
    # Arrange
    from weatherstar_4000 import animated_icons

    monkeypatch.setattr(animated_icons, "Image", None)

    # Act
    with caplog.at_level(logging.WARNING):
        icon = AnimatedIcon(str(icon_dir / "Clear.gif"))

    # Assert
    assert icon.static_image is None or icon.frames == []


def test_load_failure_logs_warning(display, tmp_path, caplog):
    # Arrange
    bad = tmp_path / "bad.gif"
    bad.write_bytes(b"not a real gif")

    # Act
    with caplog.at_level(logging.WARNING):
        AnimatedIcon(str(bad))

    # Assert
    assert any("Failed to load" in r.message for r in caplog.records)


# --- AnimatedIconManager ---------------------------------------------------


def test_manager_missing_dir_warns(display, tmp_path, caplog):
    # Act
    with caplog.at_level(logging.WARNING):
        AnimatedIconManager(str(tmp_path / "nope"))

    # Assert
    assert any("directory not found" in r.message for r in caplog.records)


def test_manager_loads_gifs_and_pngs(icon_dir, display):
    # Act
    manager = AnimatedIconManager(str(icon_dir))

    # Assert
    assert "Clear" in manager.animated_icons
    assert "Static" in manager.static_icons
    # single-frame gif is stored as an icon too but treated as static internally
    assert "Single" in manager.animated_icons


def test_manager_get_icon_animated(icon_dir, display):
    # Arrange
    manager = AnimatedIconManager(str(icon_dir))

    # Act
    icon = manager.get_icon("Clear")

    # Assert
    assert icon is not None


def test_manager_get_icon_scaled(icon_dir, display):
    # Arrange
    manager = AnimatedIconManager(str(icon_dir))

    # Act
    icon = manager.get_icon("Clear", width=30, height=30)

    # Assert
    assert icon.get_size() == (30, 30)


def test_manager_get_icon_static(icon_dir, display):
    # Arrange
    manager = AnimatedIconManager(str(icon_dir))

    # Act
    icon = manager.get_icon("Static")

    # Assert
    assert icon is not None


def test_manager_get_icon_case_insensitive(icon_dir, display):
    # Arrange
    manager = AnimatedIconManager(str(icon_dir))

    # Act
    lower = manager.get_icon("clear")

    # Assert
    assert lower is not None

    # Act
    upper = manager.get_icon("static")

    # Assert
    assert upper is not None


def test_manager_get_icon_missing_returns_none(icon_dir, display):
    # Arrange
    manager = AnimatedIconManager(str(icon_dir))

    # Act
    icon = manager.get_icon("DoesNotExist")

    # Assert
    assert icon is None


def test_manager_reset_all(icon_dir, display):
    # Arrange
    manager = AnimatedIconManager(str(icon_dir))

    # Act
    manager.reset_all_animations()

    # Assert
    for icon in manager.animated_icons.values():
        assert icon.current_frame == 0
        assert icon.last_update == 0

"""Tests for the performance optimization module."""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from weatherstar_4000.performance import (
    FontCache,
    ImageCache,
    MemoryManager,
    PerformanceMonitor,
    PerformanceOptimizer,
    RenderOptimizer,
    SurfaceCache,
    get_performance_optimizer,
)

REPO_FONT = Path(__file__).resolve().parents[1] / "static_assets" / "fonts" / "Star4000.ttf"


@pytest.fixture(autouse=True)
def _clean_font_cache():
    yield
    FontCache.clear()


# --- PerformanceMonitor ----------------------------------------------------


def test_monitor_initial_state():
    # Act
    monitor = PerformanceMonitor()

    # Assert
    assert monitor.frame_count == 0
    assert monitor.fps == 0
    assert monitor.frame_times == []


def test_monitor_update_records_frame(monkeypatch):
    # Arrange
    times = iter([1.0, 1.04, 1.08])
    monkeypatch.setattr(time, "time", lambda: next(times))
    monitor = PerformanceMonitor()
    monitor.last_frame_time = 1.0

    # Act
    monitor.update()

    # Assert
    assert monitor.frame_count == 1
    assert monitor.fps == pytest.approx(25.0)


def test_monitor_update_bounds_sample_window():
    # Arrange
    monitor = PerformanceMonitor()
    monitor.max_samples = 3

    # Act
    for i in range(6):
        monitor.last_frame_time = 1.0 + i * 0.01
        with patch("time.time", return_value=1.0 + (i + 1) * 0.01):
            monitor.update()

    # Assert
    assert len(monitor.frame_times) <= 3


def test_monitor_fps_zero_when_no_elapsed(monkeypatch):
    # Arrange
    monkeypatch.setattr(time, "time", lambda: 5.0)
    monitor = PerformanceMonitor()
    monitor.last_frame_time = 5.0

    # Act
    monitor.update()

    # Assert
    assert monitor.fps == 0


def test_get_fps_returns_value():
    # Arrange
    monitor = PerformanceMonitor()
    monitor.fps = 30

    # Act
    result = monitor.get_fps()

    # Assert
    assert result == 30


def test_get_memory_usage_returns_int():
    # Arrange
    monitor = PerformanceMonitor()

    # Act
    result = monitor.get_memory_usage()

    # Assert
    assert isinstance(result, int)


# --- SurfaceCache ----------------------------------------------------------


def test_cache_get_missing_returns_none():
    # Arrange
    cache = SurfaceCache(max_size=3)

    # Act
    result = cache.get("missing")

    # Assert
    assert result is None


def test_cache_put_and_get(display):
    # Arrange
    surface = pygame_surface(10, 10)
    cache = SurfaceCache(max_size=3)

    # Act
    cache.put("k", surface)

    # Assert
    assert cache.get("k") is not None


def test_cache_evicts_least_recently_used(display, monkeypatch):
    # Arrange
    clock = iter([1.0, 2.0, 3.0, 4.0])
    monkeypatch.setattr(time, "time", lambda: next(clock))
    cache = SurfaceCache(max_size=2)

    # Act
    cache.put("a", pygame_surface(5, 5))  # accessed at t=1
    cache.put("b", pygame_surface(5, 5))  # accessed at t=2
    cache.get("a")  # touch "a" at t=3 so "b" (t=2) becomes LRU
    cache.put("c", pygame_surface(5, 5))  # evicts "b" at t=4

    # Assert
    assert "b" not in cache.cache
    assert "a" in cache.cache
    assert "c" in cache.cache


def test_cache_clear():
    # Arrange
    cache = SurfaceCache(max_size=3)
    cache.put("a", pygame_surface_plain())

    # Act
    cache.clear()

    # Assert
    assert cache.cache == {}
    assert cache.access_times == {}


# --- FontCache -------------------------------------------------------------


def test_font_cache_uses_sysfont_when_no_path(display):
    # Act
    font = FontCache.get_font(None, 24)

    # Assert
    assert isinstance(font, pygame_font_type())


def test_font_cache_reuses_same_object(display):
    # Act
    font1 = FontCache.get_font(None, 24)
    font2 = FontCache.get_font(None, 24)

    # Assert
    assert font1 is font2


def test_font_cache_clear(display):
    # Arrange
    FontCache.get_font(None, 12)

    # Act
    FontCache.clear()

    # Assert
    assert FontCache._fonts == {}


def test_font_cache_loads_from_path(display):
    import pygame

    # Act
    font = FontCache.get_font(str(REPO_FONT), 20)

    # Assert
    assert isinstance(font, pygame.font.Font)


def test_font_cache_falls_back_when_load_fails(display):
    # Act
    font = FontCache.get_font("/nonexistent/font.ttf", 20)

    # Assert
    assert isinstance(font, pygame_font_type())


# --- ImageCache ------------------------------------------------------------


def test_image_cache_returns_cached(display, tmp_path):
    # Arrange
    path = _make_png(tmp_path, alpha=True)
    cache = ImageCache(max_size=3)

    # Act
    first = cache.load_image(str(path))
    second = cache.load_image(str(path))

    # Assert
    assert first is second


def test_image_cache_loads_and_scales(display, tmp_path):
    # Arrange
    path = _make_png(tmp_path, alpha=False)
    cache = ImageCache(max_size=3)

    # Act
    image = cache.load_image(str(path), scale=(4, 4))

    # Assert
    assert image is not None
    assert image.get_size() == (4, 4)


def test_image_cache_returns_none_on_error(display, capsys):
    # Arrange
    cache = ImageCache(max_size=3)

    # Act
    result = cache.load_image("/nonexistent.png")

    # Assert
    assert result is None
    assert "Error loading image" in capsys.readouterr().out


def test_image_cache_respects_max_size(display, tmp_path):
    # Arrange
    path = _make_png(tmp_path, alpha=False)
    cache = ImageCache(max_size=1)

    # Act
    first = cache.load_image(str(path))
    cache.load_image(str(path))
    cache.load_image(str(path))  # should not be cached

    # Assert
    assert first in cache.cache.values()


def test_image_cache_clear(display):
    # Act
    cache = ImageCache(max_size=3)

    # Assert
    assert cache.cache == {}


# --- RenderOptimizer -------------------------------------------------------


def test_optimizer_dirty_rects(display):
    # Arrange
    optimizer = RenderOptimizer()
    rect = pygame_rect()

    # Act
    optimizer.add_dirty_rect(rect)

    # Assert
    assert optimizer.get_dirty_rects() == [rect]

    # Act
    optimizer.clear_dirty_rects()

    # Assert
    assert optimizer.get_dirty_rects() == []


def test_optimize_surface_with_alpha(display):
    import pygame

    # Arrange
    surface = pygame.Surface((5, 5), pygame.SRCALPHA)

    # Act
    optimized = RenderOptimizer.optimize_surface(surface)

    # Assert
    assert optimized is not None


def test_optimize_surface_without_alpha(display):
    # Arrange
    surface = pygame_surface(5, 5)

    # Act
    optimized = RenderOptimizer.optimize_surface(surface)

    # Assert
    assert optimized is not None


def test_create_gradient_cached(display):
    # Act
    gradient = RenderOptimizer.create_gradient_cached(10, 10, (0, 0, 0), (255, 255, 255))

    # Assert
    assert gradient.get_size() == (10, 10)


# --- MemoryManager ---------------------------------------------------------


def test_memory_manager_interval_configuration():
    # Act
    manager = MemoryManager(gc_interval=60)

    # Assert
    assert manager.gc_interval == 60


def test_periodic_cleanup_runs_gc(display):
    # Arrange
    manager = MemoryManager(gc_interval=0)

    # Act
    manager.periodic_cleanup()

    # Assert
    assert manager.last_gc_time > 0


def test_periodic_cleanup_skips_when_recent(display):
    # Arrange
    manager = MemoryManager(gc_interval=300)
    manager.periodic_cleanup()
    last = manager.last_gc_time

    # Act
    manager.periodic_cleanup()

    # Assert
    assert manager.last_gc_time == last


def test_emergency_cleanup(display):
    # Act
    MemoryManager(gc_interval=300).emergency_cleanup()


# --- PerformanceOptimizer --------------------------------------------------


def test_optimizer_initial_state():
    # Act
    optimizer = PerformanceOptimizer()

    # Assert
    assert isinstance(optimizer.monitor, PerformanceMonitor)
    assert isinstance(optimizer.surface_cache, SurfaceCache)
    assert optimizer.frame_skip == 0


def test_optimizer_update_skips_frames_on_low_fps(monkeypatch):
    # Arrange
    optimizer = PerformanceOptimizer()
    optimizer.monitor.get_fps = lambda: 5  # well below 70% of 30

    # Act
    optimizer.update(target_fps=30)

    # Assert
    assert optimizer.frame_skip == 1


def test_optimizer_update_no_skip_on_healthy_fps(monkeypatch):
    # Arrange
    optimizer = PerformanceOptimizer()
    optimizer.monitor.get_fps = lambda: 60

    # Act
    optimizer.update(target_fps=30)

    # Assert
    assert optimizer.frame_skip == 0


def test_should_skip_frame_even_toggle():
    # Arrange
    optimizer = PerformanceOptimizer()
    optimizer.frame_skip = 1

    # Act
    first = optimizer.should_skip_frame()

    # Assert
    assert first is False  # count becomes 1 -> odd

    # Act
    second = optimizer.should_skip_frame()

    # Assert
    assert second is True  # count becomes 2 -> even


def test_should_skip_frame_disabled():
    # Arrange
    optimizer = PerformanceOptimizer()
    optimizer.frame_skip = 0

    # Act
    result = optimizer.should_skip_frame()

    # Assert
    assert result is False


def test_get_stats(monkeypatch):
    # Arrange
    optimizer = PerformanceOptimizer()
    optimizer.update()

    # Act
    stats = optimizer.get_stats()

    # Assert
    assert set(stats) == {
        "fps",
        "frame_count",
        "memory_estimate",
        "cache_size",
        "image_cache_size",
    }
    assert isinstance(stats["fps"], float)


def test_singleton():
    # Assert
    assert get_performance_optimizer() is get_performance_optimizer()


# --- helpers ---------------------------------------------------------------


def pygame_surface(w, h):
    import pygame

    return pygame.Surface((w, h))


def pygame_surface_plain():
    import pygame

    return pygame.Surface((5, 5))


def pygame_rect():
    import pygame

    return pygame.Rect(0, 0, 10, 10)


def pygame_font_type():
    import pygame

    return pygame.font.Font


def _make_png(tmp_path, alpha):
    import pygame

    target = tmp_path / ("alpha.png" if alpha else "plain.png")
    surface = pygame.Surface((8, 8), pygame.SRCALPHA if alpha else 0)
    surface.fill((255, 0, 0, 128) if alpha else (255, 0, 0))
    pygame.image.save(surface, str(target))
    return target

"""Tests for the severe-weather alert display module."""

from types import SimpleNamespace
from unittest.mock import Mock

import pygame

from weatherstar_4000.display_history import draw_severe_weather_alert
from weatherstar_4000.themes import CLASSIC_THEME


def _make_ws(screen, weather_data, severe_display=None):
    return SimpleNamespace(
        screen=screen,
        weather_data=weather_data,
        current_theme=CLASSIC_THEME,
        severe_weather_display=severe_display,
    )


def test_draws_all_clear_when_no_alerts(screen, pygame_env):
    # Arrange
    ws = _make_ws(screen, {"properties": {}}, severe_display=Mock())

    # Act
    draw_severe_weather_alert(ws, dt=0.016)

    # Assert
    ws.severe_weather_display.set_alerts.assert_not_called()


def test_draws_alerts_when_present(screen, pygame_env):
    # Arrange
    alerts = [{"event": "Tornado Warning"}]
    severe_display = Mock()
    ws = _make_ws(screen, {"properties": {"alerts": alerts}}, severe_display=severe_display)

    # Act
    draw_severe_weather_alert(ws, dt=0.016)

    # Assert
    severe_display.set_alerts.assert_called_once_with(alerts)
    severe_display.draw_full_alert_screen.assert_called_once()


def test_handles_missing_weather_data(screen, pygame_env):
    # Arrange
    severe_display = Mock()
    ws = _make_ws(screen, {}, severe_display=severe_display)

    # Act
    draw_severe_weather_alert(ws, dt=0.016)

    # Assert
    severe_display.set_alerts.assert_not_called()


def test_pixel_fill_in_all_clear_path(screen, pygame_env):
    # Arrange
    ws = _make_ws(screen, {"properties": {}}, severe_display=Mock())

    # Act
    draw_severe_weather_alert(ws, dt=0.016)

    # Assert
    # bg fill is dark gradient blue at the corners
    assert screen.get_at((0, 0))[:3] == CLASSIC_THEME.get_color("blue_gradient_2")


def test_render_failure_is_swallowed(screen, pygame_env, monkeypatch):
    # Arrange
    ws = _make_ws(screen, {"properties": {}}, severe_display=Mock())
    original_font = pygame.font.Font

    def exploding_font(*args, **kwargs):
        raise RuntimeError("font broke")

    monkeypatch.setattr(pygame.font, "Font", exploding_font)

    # Act
    draw_severe_weather_alert(ws, dt=0.016)

    monkeypatch.setattr(pygame.font, "Font", original_font)

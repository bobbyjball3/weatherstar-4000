"""Tests for the emergency alert animation module."""

import pygame
import pytest

from weatherstar_4000.emergency_animations import (
    EmergencyAlertAnimator,
    SevereWeatherDisplay,
    get_alert_animator,
)


@pytest.fixture()
def animator():
    return EmergencyAlertAnimator()


def _font():
    return pygame.font.Font(None, 20)


# --- EmergencyAlertAnimator ------------------------------------------------


def test_initial_state(animator):
    # Assert
    assert animator.alert_active is False
    assert animator.flash_state is False
    assert animator.scroll_offset == 0


def test_set_alert_active_resets_scroll(animator):
    # Arrange
    animator.scroll_offset = 55

    # Act
    animator.set_alert(True)

    # Assert
    assert animator.alert_active is True
    assert animator.scroll_offset == 0


def test_set_alert_inactive(animator):
    # Act
    animator.set_alert(False)

    # Assert
    assert animator.alert_active is False


def test_update_toggles_flash_and_advances_scroll(animator, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 1.0)  # 1000 ms
    animator.last_flash_time = 0

    # Act
    animator.update(dt=0.5)

    # Assert
    assert animator.flash_state is True
    assert animator.scroll_offset == pytest.approx(25.0)  # 50 px/s * 0.5s


def test_update_does_not_toggle_flash_early(animator, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 0.2)  # 200 ms
    animator.last_flash_time = 0

    # Act
    animator.update(dt=0.1)

    # Assert
    assert animator.flash_state is False


def test_draw_flashing_border_inactive(screen):
    # Arrange
    animator = EmergencyAlertAnimator()

    # Act
    animator.draw_flashing_border(screen, pygame.Rect(0, 0, 10, 10))

    # Assert
    assert screen.get_at((5, 5))[:3] == (0, 0, 0)  # untouched black surface


def test_draw_flashing_border_when_flashing(screen, display):
    # Arrange
    animator = EmergencyAlertAnimator()
    animator.set_alert(True)
    animator.flash_state = True

    # Act
    animator.draw_flashing_border(screen, pygame.Rect(0, 0, 20, 20), (255, 0, 0), 2)

    # Assert
    assert screen.get_at((0, 0))[:3] == (255, 0, 0)


def test_draw_flashing_border_when_not_flashing(screen):
    # Arrange
    animator = EmergencyAlertAnimator()
    animator.set_alert(True)
    animator.flash_state = False

    # Act
    animator.draw_flashing_border(screen, pygame.Rect(0, 0, 20, 20), (255, 0, 0), 2)

    # Assert
    assert screen.get_at((0, 0))[:3] == (0, 0, 0)


def test_draw_scrolling_text_inactive(screen):
    # Arrange
    animator = EmergencyAlertAnimator()

    # Act
    animator.draw_scrolling_text(screen, pygame.Rect(0, 0, 200, 30), "text", _font())

    # Assert
    assert screen.get_at((0, 0))[:3] == (0, 0, 0)


def test_draw_scrolling_text_empty(screen):
    # Arrange
    animator = EmergencyAlertAnimator()
    animator.set_alert(True)

    # Act
    animator.draw_scrolling_text(screen, pygame.Rect(0, 0, 200, 30), "", _font())

    # Assert
    assert screen.get_at((0, 0))[:3] == (0, 0, 0)


def test_draw_scrolling_text_draws_and_loops(screen, display):
    # Arrange
    animator = EmergencyAlertAnimator()
    animator.set_alert(True)
    animator.scroll_offset = 50

    # Act
    animator.draw_scrolling_text(screen, pygame.Rect(0, 0, 100, 30), "warning text", _font())

    # Assert
    # top-left of the ticker band was painted
    assert screen.get_at((0, 15))[:3] == (139, 0, 0)


def test_draw_alert_header_inactive(screen):
    # Arrange
    animator = EmergencyAlertAnimator()

    # Act
    animator.draw_alert_header(screen, pygame.Rect(0, 0, 100, 40), "ALERT", _font())

    # Assert
    assert screen.get_at((50, 20))[:3] == (0, 0, 0)


def test_draw_alert_header_active(screen, monkeypatch):
    # Arrange
    animator = EmergencyAlertAnimator()
    animator.set_alert(True)
    monkeypatch.setattr("time.time", lambda: 1.0)

    # Act
    animator.draw_alert_header(screen, pygame.Rect(0, 0, 200, 40), "ALERT", _font())

    # Assert
    assert screen.get_at((100, 20))[:3] != (0, 0, 0)


def test_draw_alert_header_flash_border(screen, monkeypatch):
    # Arrange
    animator = EmergencyAlertAnimator()
    animator.set_alert(True)
    animator.flash_state = True
    monkeypatch.setattr("time.time", lambda: 1.0)

    # Act
    animator.draw_alert_header(screen, pygame.Rect(0, 0, 100, 40), "ALERT", _font())


def test_draw_blinking_indicator_inactive(screen):
    # Arrange
    animator = EmergencyAlertAnimator()

    # Act
    animator.draw_blinking_indicator(screen, (50, 50))

    # Assert
    assert screen.get_at((50, 50))[:3] == (0, 0, 0)


def test_draw_blinking_indicator_flashing(screen):
    # Arrange
    animator = EmergencyAlertAnimator()
    animator.set_alert(True)
    animator.flash_state = True

    # Act
    animator.draw_blinking_indicator(screen, (50, 50), radius=10, color=(255, 0, 0))

    # Assert
    assert screen.get_at((50, 50))[:3] == (255, 0, 0)


def test_reset(animator):
    # Arrange
    animator.set_alert(True)
    animator.scroll_offset = 123
    animator.flash_state = True

    # Act
    animator.reset()

    # Assert
    assert animator.scroll_offset == 0
    assert animator.flash_state is False
    assert animator.alert_active is False


def test_get_alert_animator_singleton():
    # Assert
    assert get_alert_animator() is get_alert_animator()


# --- SevereWeatherDisplay --------------------------------------------------


@pytest.fixture()
def severe():
    return SevereWeatherDisplay()


def test_severe_set_alerts_empty(severe):
    # Act
    severe.set_alerts([])

    # Assert
    assert severe.current_alerts == []
    assert severe.animator.alert_active is False


def test_severe_set_alerts_nonempty(severe):
    # Act
    severe.set_alerts([{"event": "Tornado"}])

    # Assert
    assert severe.animator.alert_active is True


def test_severe_load_fonts(severe, display):
    # Act
    severe.load_fonts()

    # Assert
    assert severe.alert_font_large is not None
    assert severe.alert_font_small is not None


def test_severe_load_fonts_fallback(screen, monkeypatch):
    # Arrange
    severe = SevereWeatherDisplay()
    original_font = pygame.font.Font
    monkeypatch.setattr(pygame.font, "Font", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **k: original_font(None, 20))

    # Act
    severe.load_fonts()

    # Assert
    assert severe.alert_font_large is not None


def test_severe_draw_empty_alerts_returns(screen):
    # Arrange
    severe = SevereWeatherDisplay()

    # Act
    result = severe.draw_full_alert_screen(screen, 0.016, {})

    # Assert
    assert result is None


def test_severe_draw_full_alert_screen(screen, display):
    # Arrange
    severe = SevereWeatherDisplay()
    severe.set_alerts(
        [
            {
                "event": "TORNADO WARNING",
                "headline": "Tornado warning issued for the county",
                "description": "A tornado has been spotted. Take shelter immediately. " * 3,
            }
        ]
    )

    # Act
    result = severe.draw_full_alert_screen(screen, 0.016, {})

    # Assert
    assert result is None

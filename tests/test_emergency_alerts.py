"""Tests for the emergency weather alert system."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from weatherstar_4000.emergency_alerts import (
    ALERT_COLORS,
    URGENCY_PRIORITY,
    EmergencyAlertSystem,
)


@pytest.fixture()
def system(pygame_env):
    return EmergencyAlertSystem(40.0, -74.0)


def _feature(event, severity, urgency="Immediate"):
    return {
        "properties": {
            "id": f"id-{event}",
            "event": event,
            "severity": severity,
            "urgency": urgency,
            "certainty": "Observed",
            "headline": f"{event} headline",
            "description": f"{event} description",
            "instruction": "Take shelter",
            "areaDesc": "Anytown, USA",
            "effective": "2026-01-01T00:00:00-05:00",
            "expires": "2026-01-01T12:00:00-05:00",
        }
    }


def _alert(severity="Severe", event="Storm", urgency="Immediate", **overrides):
    alert = {
        "severity": severity,
        "event": event,
        "urgency": urgency,
        "certainty": "Observed",
        "headline": f"{event} headline",
        "description": f"{event} description",
        "instruction": "Take shelter now",
        "areas": "Anytown, USA",
        "effective": "2026-01-01T00:00:00-05:00",
        "expires": "2026-01-01T12:00:00-05:00",
    }
    alert.update(overrides)
    return alert


# --- check_for_alerts ------------------------------------------------------


def test_check_throttled_with_no_alerts(system, monkeypatch):
    # Arrange
    monkeypatch.setattr("time.time", lambda: 500.0)
    system.last_check = 500.0

    # Act
    result = system.check_for_alerts()

    # Assert
    assert result is False


def test_check_throttled_returns_active(system, monkeypatch):
    # Arrange
    system.active_alerts = [{"event": "Tornado"}]
    monkeypatch.setattr("time.time", lambda: 500.0)
    system.last_check = 500.0

    # Act
    result = system.check_for_alerts()

    # Assert
    assert result is True


def test_check_filters_and_plays_sound(system, monkeypatch):
    # Arrange
    system.alert_sound = Mock()
    system.check_interval = 0
    response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "features": [
                _feature("Tornado Warning", "Severe", "Immediate"),
                _feature("Flood Watch", "Moderate", "Expected"),
                _feature("Minor Blip", "Minor"),  # filtered out
                _feature("Heat Advisory", "Unknown"),  # filtered out
            ]
        },
    )
    monkeypatch.setattr("time.time", lambda: 500.0)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("requests.get", Mock(return_value=response))

        # Act
        result = system.check_for_alerts()

    # Assert
    assert result is True
    assert system.alert_shown is True
    assert len(system.active_alerts) == 2
    system.alert_sound.play.assert_called_once()
    assert [a["event"] for a in system.active_alerts] == ["Tornado Warning", "Flood Watch"]


def test_check_sorts_by_urgency_then_severity(system, monkeypatch):
    # Arrange
    system.check_interval = 0
    response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "features": [
                _feature("Flash Flood", "Severe", "Expected"),
                _feature("Blizzard", "Extreme", "Future"),
            ]
        },
    )
    monkeypatch.setattr("time.time", lambda: 500.0)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("requests.get", Mock(return_value=response))

        # Act
        system.check_for_alerts()

    # Assert
    assert system.active_alerts[0]["event"] == "Flash Flood"  # Expected urgency beats Future


def test_check_no_sound_when_already_shown(system, monkeypatch):
    # Arrange
    system.alert_sound = Mock()
    system.alert_shown = True
    system.check_interval = 0
    response = SimpleNamespace(
        status_code=200,
        json=lambda: {"features": [_feature("Warning", "Severe")]},
    )
    monkeypatch.setattr("time.time", lambda: 500.0)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("requests.get", Mock(return_value=response))

        # Act
        system.check_for_alerts()

    # Assert
    system.alert_sound.play.assert_not_called()


def test_check_returns_false_on_bad_status(system, monkeypatch):
    # Arrange
    system.check_interval = 0
    monkeypatch.setattr("time.time", lambda: 500.0)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("requests.get", Mock(return_value=SimpleNamespace(status_code=500)))

        # Act
        result = system.check_for_alerts()

    # Assert
    assert result is False
    assert system.active_alerts == []


def test_check_returns_false_on_exception(system, monkeypatch):
    # Arrange
    system.check_interval = 0
    monkeypatch.setattr("time.time", lambda: 500.0)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("requests.get", Mock(side_effect=Exception("down")))

        # Act
        result = system.check_for_alerts()

    # Assert
    assert result is False
    assert system.active_alerts == []


# --- sounds ----------------------------------------------------------------


def test_play_alert_sound_beeps_when_no_sound_file(system, capsys):
    # Arrange
    system.alert_sound = None

    # Act
    system.play_alert_sound()

    # Assert
    assert "\a" in capsys.readouterr().out


def test_play_alert_sound_plays_sound(system):
    # Arrange
    system.alert_sound = Mock()

    # Act
    system.play_alert_sound()

    # Assert
    system.alert_sound.play.assert_called_once()


def test_play_alert_sound_swallows_errors(system):
    # Arrange
    system.alert_sound = Mock()
    system.alert_sound.play.side_effect = Exception("audio broke")

    # Act
    system.play_alert_sound()  # should not raise


# --- drawing ---------------------------------------------------------------


def test_draw_returns_false_without_alerts(system, screen):
    # Assert
    assert system.draw_emergency_screen(screen, {}) is False


def test_draw_emergency_screen_extreme(system, screen, fonts):
    # Arrange
    system.active_alerts = [
        _alert(severity="Extreme", event="Tornado", headline="H", areas="", instruction="")
    ]

    # Act
    result = system.draw_emergency_screen(screen, fonts)

    # Assert
    assert result is True


def test_draw_emergency_screen_without_fonts(system, screen):
    # Arrange
    system.active_alerts = [_alert(severity="Severe", event="Storm")]

    # Act
    result = system.draw_emergency_screen(screen, {})

    # Assert
    assert result is True


def test_draw_wraps_text_and_parses_expiry(system, screen, fonts):
    # Arrange
    system.active_alerts = [
        _alert(
            severity="Moderate",
            event="Flood",
            headline="long headline " * 30,
            areas="County A, County B " * 20,
            instruction="Move to higher ground now " * 25,
            expires="2026-01-01T12:00:00+00:00",
        )
    ]

    # Act
    result = system.draw_emergency_screen(screen, fonts)

    # Assert
    assert result is True


def test_draw_ignores_invalid_expiry(system, screen, fonts):
    # Arrange
    system.active_alerts = [_alert(severity="Severe", event="Storm", expires="not-a-date")]

    # Act
    result = system.draw_emergency_screen(screen, fonts)

    # Assert
    assert result is True


def test_draw_shows_counter_when_multiple(system, screen, fonts):
    # Arrange
    system.active_alerts = [
        _alert(severity="Moderate", event="A"),
        _alert(severity="Severe", event="B"),
    ]

    # Act
    result = system.draw_emergency_screen(screen, fonts)

    # Assert
    assert result is True


# --- rotation / criticality / summary --------------------------------------


def test_update_alert_display_rotates(system, monkeypatch):
    # Arrange
    system.active_alerts = [{"a": 1}, {"b": 2}]
    monkeypatch.setattr("time.time", lambda: 500.0)
    system.alert_display_time = 0.0

    # Act
    system.update_alert_display()

    # Assert
    assert system.current_alert_index == 1
    assert system.alert_display_time == 500.0


def test_update_alert_display_skips_rotation_within_window(system, monkeypatch):
    # Arrange
    system.active_alerts = [{"a": 1}, {"b": 2}]
    monkeypatch.setattr("time.time", lambda: 500.0)
    system.alert_display_time = 495.0

    # Act
    system.update_alert_display()

    # Assert
    assert system.current_alert_index == 0


def test_update_alert_display_single_alert_no_rotation(system, monkeypatch):
    # Arrange
    system.active_alerts = [{"a": 1}]
    monkeypatch.setattr("time.time", lambda: 500.0)
    system.alert_display_time = 0.0

    # Act
    system.update_alert_display()

    # Assert
    assert system.current_alert_index == 0


@pytest.mark.parametrize(
    "alerts, expected",
    [
        ([{"severity": "Extreme"}], True),
        ([{"severity": "Severe", "urgency": "Immediate"}], True),
        ([{"severity": "Severe", "urgency": "Expected"}], False),
        ([{"severity": "Moderate"}], False),
        ([], False),
    ],
)
def test_has_critical_alert(alerts, expected):
    # Arrange
    system = EmergencyAlertSystem(0.0, 0.0)
    system.active_alerts = alerts

    # Act
    result = system.has_critical_alert()

    # Assert
    assert result is expected


def test_alert_summary_empty_without_alerts():
    # Arrange
    system = EmergencyAlertSystem(0.0, 0.0)

    # Act
    summary = system.get_alert_summary()

    # Assert
    assert summary == ""


def test_alert_summary_builds_text():
    # Arrange
    system = EmergencyAlertSystem(0.0, 0.0)
    system.active_alerts = [
        {"severity": "Severe", "event": "Tornado"},
        {"severity": "Moderate", "event": "Flood"},
        {"severity": "Extreme", "event": "Blizzard"},
    ]

    # Act
    summary = system.get_alert_summary()

    # Assert
    assert "WEATHER ALERT" in summary
    assert "Severe Tornado" in summary
    assert "Extreme Blizzard" in summary


def test_alert_summary_limits_to_three():
    # Arrange
    system = EmergencyAlertSystem(0.0, 0.0)
    system.active_alerts = [{"severity": "Severe", "event": f"E{i}"} for i in range(5)]

    # Act
    summary = system.get_alert_summary()

    # Assert
    assert summary.count("Severe E") == 3


# --- constants -------------------------------------------------------------


def test_alert_colors_cover_all_severities():
    # Assert
    for severity in ["Extreme", "Severe", "Moderate", "Minor", "Unknown"]:
        assert severity in ALERT_COLORS


def test_urgency_priority_ordering():
    # Assert
    assert URGENCY_PRIORITY["Immediate"] > URGENCY_PRIORITY["Expected"]
    assert URGENCY_PRIORITY["Expected"] > URGENCY_PRIORITY["Future"]
    assert URGENCY_PRIORITY["Future"] > URGENCY_PRIORITY["Past"]
    assert URGENCY_PRIORITY["Past"] > URGENCY_PRIORITY["Unknown"]

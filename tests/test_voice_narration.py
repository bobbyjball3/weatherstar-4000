"""Tests for the voice narration module (pyttsx3 fully mocked)."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import weatherstar_4000.voice_narration as vn
from weatherstar_4000.voice_narration import VoiceNarrator


@pytest.fixture()
def fake_engine(monkeypatch):
    """Return a fake pyttsx3 engine and wire pyttsx3.init to it."""
    import pyttsx3

    engine = Mock()
    engine.getProperty.return_value = [
        SimpleNamespace(name="Zira Female", id="female-id"),
        SimpleNamespace(name="Daniel Male Voice", id="male-id"),
    ]
    monkeypatch.setattr(pyttsx3, "init", lambda *a, **kw: engine)
    return engine


@pytest.fixture()
def narrator(fake_engine):
    return VoiceNarrator()


# --- initialization --------------------------------------------------------


def test_init_initializes_engine_and_sets_properties(narrator, fake_engine):
    # Assert
    assert narrator.tts_engine is fake_engine
    assert narrator.enabled is False
    assert narrator.min_announcement_interval == 2.0
    # Configured rate and volume
    fake_engine.setProperty.assert_any_call("rate", 150)
    fake_engine.setProperty.assert_any_call("volume", 0.9)


def test_init_selects_male_voice(narrator, fake_engine):
    # Assert
    selected = [c[0][1] for c in fake_engine.setProperty.call_args_list if c[0][0] == "voice"]
    assert selected == ["male-id"]


def test_init_handles_import_error(monkeypatch):
    # Arrange
    import pyttsx3

    def raise_import(*a, **kw):
        raise ImportError("no tts")

    monkeypatch.setattr(pyttsx3, "init", raise_import)

    # Act
    narrator = VoiceNarrator()

    # Assert
    assert narrator.tts_engine is None
    assert narrator.is_available() is False


def test_init_handles_generic_error(monkeypatch):
    # Arrange
    import pyttsx3

    monkeypatch.setattr(pyttsx3, "init", Mock(side_effect=RuntimeError("boom")))

    # Act
    narrator = VoiceNarrator()

    # Assert
    assert narrator.tts_engine is None


# --- enable / callbacks ----------------------------------------------------


def test_set_enabled_disabled_does_not_reinit(narrator):
    # Act
    narrator.set_enabled(False)

    # Assert
    assert narrator.enabled is False


def test_set_enabled_enables_when_engine_present(narrator):
    # Act
    narrator.set_enabled(True)

    # Assert
    assert narrator.enabled is True


def test_is_available_reflects_engine(narrator):
    # Act
    available = narrator.is_available()

    # Assert
    assert available is True

    # Arrange
    narrator.tts_engine = None

    # Act
    available = narrator.is_available()

    # Assert
    assert available is False


def test_set_audio_callbacks_stores(narrator):
    # Arrange
    duck, restore = Mock(), Mock()

    # Act
    narrator.set_audio_callbacks(duck, restore)

    # Assert
    assert narrator.duck_callback is duck
    assert narrator.restore_callback is restore


# --- _speak_async ----------------------------------------------------------


def test_speak_async_returns_when_disabled(narrator):
    # Arrange
    narrator.set_enabled(False)

    # Act
    narrator._speak_async("hello")

    # Assert
    assert narrator.speech_thread is None


def test_speak_async_returns_when_no_engine(narrator):
    # Arrange
    narrator.set_enabled(True)
    narrator.tts_engine = None

    # Act
    narrator._speak_async("hello")

    # Assert
    assert narrator.speech_thread is None


def test_speak_async_returns_when_blank_text(narrator):
    # Arrange
    narrator.set_enabled(True)

    # Act
    narrator._speak_async("")

    # Assert
    assert narrator.speech_thread is None


def test_speak_async_rate_limits(narrator, fake_engine):
    # Arrange
    narrator.set_enabled(True)
    narrator.last_announcement_time = 9999999999

    # Act
    narrator._speak_async("hello")

    # Assert
    assert narrator.speech_thread is None


def test_speak_async_duck_and_restore(narrator, fake_engine, monkeypatch):
    # Arrange
    class FakeThread:
        def __init__(self, target, daemon=False):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(vn.threading, "Thread", FakeThread)
    duck, restore = Mock(), Mock()
    narrator.set_audio_callbacks(duck, restore)
    narrator.set_enabled(True)

    # Act
    narrator._speak_async("weather update")

    # Assert
    duck.assert_called_once()
    restore.assert_called_once()
    fake_engine.say.assert_called_once_with("weather update")
    fake_engine.runAndWait.assert_called_once()


def test_speak_async_handles_engine_error(narrator, fake_engine, monkeypatch):
    # Arrange
    class FakeThread:
        def __init__(self, target, daemon=False):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(vn.threading, "Thread", FakeThread)
    fake_engine.runAndWait.side_effect = RuntimeError("speech failed")
    restore = Mock()
    narrator.set_audio_callbacks(None, restore)
    narrator.set_enabled(True)

    # Act
    narrator._speak_async("hello")

    # Assert
    assert narrator.is_speaking is False
    restore.assert_called_once()


# --- announcements ---------------------------------------------------------


def test_announce_display_returns_when_disabled(narrator):
    # Arrange
    narrator._speak_async = Mock()

    # Act
    narrator.announce_display("radar")

    # Assert
    narrator._speak_async.assert_not_called()


@pytest.mark.parametrize(
    "mode, expected_fragment",
    [
        ("local-forecast", "local forecast"),
        ("extended-forecast", "seven day forecast"),
        ("hourly-forecast", "twenty four hours"),
        ("regional-observations", "Regional weather observations"),
        ("travel-cities", "Travel forecast"),
        ("almanac", "Weather almanac"),
        ("radar", "Local weather radar"),
        ("hazards", "Active weather hazards"),
        ("marine-forecast", "Marine forecast"),
        ("air-quality", "Air quality"),
        ("temperature-graph", "temperature trend"),
        ("history-graphs", "Thirty day weather history"),
        ("weather-records", "Record temperatures"),
        ("sun-moon", "Sun and moon"),
        ("wind-pressure", "Wind and barometric pressure"),
        ("weekend-forecast", "weekend forecast"),
        ("monthly-outlook", "Monthly weather outlook"),
        ("msn-news", "Top news headlines"),
        ("reddit-news", "Trending headlines"),
        ("local-news", "Local news"),
        ("severe-weather-alert", "Severe weather alert"),
        ("unknown-mode", ""),
    ],
)
def test_generate_announcement_for_modes(narrator, mode, expected_fragment):
    # Act
    text = narrator._generate_announcement(mode, None)

    # Assert
    assert expected_fragment in text


def test_announce_display_speaks_announcement(narrator):
    # Arrange
    narrator.set_enabled(True)
    narrator._speak_async = Mock()

    # Act
    narrator.announce_display("radar")

    # Assert
    narrator._speak_async.assert_called_once_with("Local weather radar.")


# --- current conditions narration -------------------------------------------


def test_current_conditions_none_data(narrator):
    # Assert
    assert narrator._announce_current_conditions(None) == "Current weather conditions."


def test_current_conditions_empty_data(narrator):
    # Assert
    assert narrator._announce_current_conditions({}) == "Current weather conditions."


def test_current_conditions_full(narrator):
    # Arrange
    data = {
        "properties": {
            "temperature": {"value": 20},  # 68F
            "textDescription": "Partly Cloudy",
            "windSpeed": {"value": 16},  # ~10 mph
            "windDirection": {"value": 90},  # east
            "relativeHumidity": {"value": 55},
        }
    }

    # Act
    text = narrator._announce_current_conditions(data)

    # Assert
    assert "68 degrees" in text
    assert "partly cloudy" in text
    assert "east" in text
    assert "Humidity 55 percent" in text


def test_current_conditions_handles_exception(narrator, monkeypatch):
    # Arrange
    data = {"properties": {"temperature": {"value": 20}, "windSpeed": {"value": 16}}}
    monkeypatch.setattr(
        vn.VoiceNarrator,
        "_wind_direction_to_text",
        lambda self, d: (_ for _ in ()).throw(ValueError("bad dir")),
    )

    # Act
    text = narrator._announce_current_conditions(data)

    # Assert
    assert text == "Current weather conditions."


@pytest.mark.parametrize(
    "degrees, expected",
    [
        (None, "unknown direction"),
        (0, "north"),
        (10, "north"),
        (30, "north northeast"),
        (45, "northeast"),
        (70, "east northeast"),
        (90, "east"),
        (110, "east southeast"),
        (135, "southeast"),
        (160, "south southeast"),
        (180, "south"),
        (200, "south southwest"),
        (225, "southwest"),
        (250, "west southwest"),
        (270, "west"),
        (290, "west northwest"),
        (315, "northwest"),
        (340, "north northwest"),
        (359, "north"),
        (360, "north"),
    ],
)
def test_wind_direction_to_text(narrator, degrees, expected):
    # Assert
    assert narrator._wind_direction_to_text(degrees) == expected


def test_announce_alert_skipped_when_disabled(narrator):
    # Arrange
    narrator._speak_async = Mock()

    # Act
    narrator.announce_alert("Tornado warning")

    # Assert
    narrator._speak_async.assert_not_called()


def test_announce_alert_when_enabled(narrator):
    # Arrange
    narrator.set_enabled(True)
    narrator._speak_async = Mock()

    # Act
    narrator.announce_alert("Tornado warning")

    # Assert
    narrator._speak_async.assert_called_once_with("Attention. Tornado warning")


def test_announce_time_skipped_when_disabled(narrator):
    # Arrange
    narrator._speak_async = Mock()

    # Act
    narrator.announce_time()

    # Assert
    narrator._speak_async.assert_not_called()


def test_announce_time_when_enabled(narrator):
    # Arrange
    narrator.set_enabled(True)
    narrator._speak_async = Mock()

    # Act
    narrator.announce_time()

    # Assert
    narrator._speak_async.assert_called_once()
    text = narrator._speak_async.call_args[0][0]
    assert text.startswith("The time is")


def test_cleanup_stops_engine(narrator, fake_engine):
    # Act
    narrator.cleanup()

    # Assert
    fake_engine.stop.assert_called_once()


def test_cleanup_no_engine():
    # Arrange
    narrator = VoiceNarrator.__new__(VoiceNarrator)
    narrator.tts_engine = None

    # Act
    narrator.cleanup()  # should not raise

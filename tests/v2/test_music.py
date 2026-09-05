"""Tests for config-driven ambient music in the engine."""

import sys

from weatherstar_4000.v2.config_file import AppConfig
from weatherstar_4000.v2.context import AppContext, DataRegistry, Location
from weatherstar_4000.v2.engine import Builder, music_enabled
from weatherstar_4000.v2.media.music import Music
from weatherstar_4000.v2.registry import discover
from weatherstar_4000.v2.sequence import Sequence

BASIC = {
    "sequences": {
        "main": {"slides": [{"screen": "progress"}]},
    },
}


def _cfg(**music_extra) -> AppConfig:
    data = dict(BASIC)
    if music_extra is not None:
        data["media"] = {"music": dict(music_extra)}
    return AppConfig(data)


def test_music_enabled_detects_config_flag():
    assert music_enabled(_cfg(enabled=True)) is True
    assert music_enabled(_cfg()) is False
    assert music_enabled(AppConfig({"media": {"music": {}}})) is False


def test_music_included_in_dependencies_when_enabled():
    discover()
    enabled = Builder(_cfg(enabled=True, volume=0.5)).sequence_dependencies(
        Sequence.from_config("main", _cfg(enabled=True).get_sequence("main"))
    )
    assert "music" in enabled["media"]
    disabled = Builder(_cfg()).sequence_dependencies(
        Sequence.from_config("main", _cfg().get_sequence("main"))
    )
    assert "music" not in disabled["media"]


class _FakeMusic:
    def __init__(self):
        self.loaded = None
        self.load_history = []
        self.volume = None
        self.played = None
        self.busy = True

    def load(self, path):
        self.loaded = path
        self.load_history.append(path)

    def set_volume(self, value):
        self.volume = value

    def play(self, loops):
        self.played = loops
        self.busy = True

    def stop(self):
        self.played = None
        self.busy = False

    def get_busy(self):
        return self.busy


class _FakeMixer:
    def __init__(self):
        self.music = _FakeMusic()
        self.inited = False

    def init(self):
        self.inited = True

    def get_init(self):
        return self.inited


def _fake_pygame(monkeypatch, fake_mixer):
    import types

    class _FakePygame(types.ModuleType):
        mixer = fake_mixer

    fake = _FakePygame("pygame")
    monkeypatch.setitem(sys.modules, "pygame", fake)
    return fake


def _make_music(enabled=True, volume=0.4, asset_dir=None) -> Music:
    values = {"enabled": enabled, "volume": volume}
    if asset_dir is not None:
        values["asset_dir"] = asset_dir
    return Music.model_validate(values)


def test_music_load_only_discovers(screen, monkeypatch, tmp_path):
    discover()
    fake = _fake_pygame(monkeypatch, _FakeMixer())
    track = tmp_path / "music" / "a.mp3"
    track.parent.mkdir()
    track.write_bytes(b"not really audio")
    ctx = AppContext(surface=screen, data=DataRegistry(), location=Location(lat=0.0, lon=0.0))
    music = _make_music(enabled=True, volume=0.4, asset_dir=str(tmp_path))
    tracks = music.load(ctx)
    assert tracks == [str(track)]
    assert ctx.assets["music"] == tracks
    assert fake.mixer.music.loaded is None


def test_music_play_starts_only_when_enabled(screen, monkeypatch):
    fake = _fake_pygame(monkeypatch, _FakeMixer())
    ctx = AppContext(surface=screen, data=DataRegistry(), location=Location(lat=0.0, lon=0.0))
    ctx.assets["music"] = ["/tmp/example.mp3"]
    disabled = _make_music(enabled=False)
    assert disabled.play(ctx) is False
    assert fake.mixer.music.loaded is None
    music = _make_music(enabled=True, volume=0.4)
    assert music.play(ctx) is True
    assert fake.mixer.music.loaded == "/tmp/example.mp3"
    assert fake.mixer.music.volume == 0.4
    assert fake.mixer.music.played == 0


def test_play_starts_from_shuffled_first_track(screen, monkeypatch):
    fake = _fake_pygame(monkeypatch, _FakeMixer())
    # Force a deterministic "shuffle": move last track to the front.
    monkeypatch.setattr(
        "weatherstar_4000.v2.media.music.random.shuffle",
        lambda seq: seq.insert(0, seq.pop()),
    )
    ctx = AppContext(surface=screen, data=DataRegistry(), location=Location(lat=0.0, lon=0.0))
    ctx.assets["music"] = ["/tmp/a.mp3", "/tmp/b.mp3", "/tmp/c.mp3"]
    music = _make_music()
    assert music.play(ctx) is True
    assert fake.mixer.music.loaded == "/tmp/c.mp3"


def test_advance_moves_through_shuffled_playlist_and_wraps(screen, monkeypatch):
    fake = _fake_pygame(monkeypatch, _FakeMixer())
    monkeypatch.setattr(
        "weatherstar_4000.v2.media.music.random.shuffle",
        lambda seq: seq.insert(0, seq.pop()),
    )
    ctx = AppContext(surface=screen, data=DataRegistry(), location=Location(lat=0.0, lon=0.0))
    ctx.assets["music"] = ["/tmp/a.mp3", "/tmp/b.mp3", "/tmp/c.mp3"]
    music = _make_music()
    music.play(ctx)
    assert fake.mixer.music.load_history == ["/tmp/c.mp3"]
    for expected in ("/tmp/a.mp3", "/tmp/b.mp3", "/tmp/c.mp3"):
        fake.mixer.music.busy = False  # current song ended
        music.advance()
        assert fake.mixer.music.loaded == expected
    assert fake.mixer.music.played == 0


def test_builder_start_music_respects_config(monkeypatch):
    discover()
    fake = _fake_pygame(monkeypatch, _FakeMixer())
    enabled = Builder(_cfg(enabled=True))
    ctx = AppContext(surface=None, data=DataRegistry(), location=Location(lat=0.0, lon=0.0))
    ctx.assets["music"] = ["/tmp/example.mp3"]
    assert enabled.start_music(ctx) is True
    assert fake.mixer.music.played == 0
    disabled = Builder(_cfg())
    assert disabled.start_music(ctx) is False


def test_builder_advance_music_delegates_to_player(screen, monkeypatch):
    discover()
    fake = _fake_pygame(monkeypatch, _FakeMixer())
    monkeypatch.setattr("weatherstar_4000.v2.media.music.random.shuffle", lambda seq: None)
    builder = Builder(_cfg(enabled=True))
    ctx = AppContext(surface=screen, data=DataRegistry(), location=Location(lat=0.0, lon=0.0))
    ctx.assets["music"] = ["/tmp/a.mp3", "/tmp/b.mp3"]
    builder.start_music(ctx)
    assert fake.mixer.music.loaded == "/tmp/a.mp3"
    fake.mixer.music.busy = False
    builder.advance_music()
    assert fake.mixer.music.loaded == "/tmp/b.mp3"

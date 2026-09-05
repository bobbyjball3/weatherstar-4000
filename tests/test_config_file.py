"""Tests for config file discovery, parsing, and sequence selection."""

import pytest

from weatherstar_4000 import ConfigError, SequenceError
from weatherstar_4000.config_file import (
    ENV_SEQUENCE,
    AppConfig,
    discover_config_path,
    load_toml,
)


def _write(tmp_path, text):
    path = tmp_path / "config.toml"
    path.write_text(text)
    return path


SAMPLE = """
sequence = "main"
[sequences.main]
pause = 15.0
slides = [{ screen = "current_conditions" }]
[sequences.from_cli]
slides = []
[sequences.from_env]
slides = []
[datasource.alpha_vantage]
api_key = "abc123"
timeout = 10
[logging]
level = "DEBUG"
console = false
"""


def test_discover_explicit_beats_env_and_default(tmp_path, monkeypatch):
    explicit = tmp_path / "explicit.toml"
    explicit.write_text("")
    monkeypatch.setenv("WEATHERSTAR_CONFIG", str(tmp_path / "env.toml"))
    assert discover_config_path(str(explicit)) == explicit


def test_discover_env_when_no_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("WEATHERSTAR_CONFIG", str(tmp_path / "env.toml"))
    assert discover_config_path() == tmp_path / "env.toml"


def test_discover_default_xdg_when_exists(tmp_path, monkeypatch):
    default = tmp_path / "cfg" / "weatherstar4000" / "config.toml"
    default.parent.mkdir(parents=True)
    default.write_text("")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("WEATHERSTAR_CONFIG", raising=False)
    assert discover_config_path() == default


def test_discover_returns_none_when_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("WEATHERSTAR_CONFIG", raising=False)
    assert discover_config_path() is None


def test_load_toml_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_toml(tmp_path / "nope.toml")


def test_load_toml_invalid_syntax_raises(tmp_path):
    path = tmp_path / "bad.toml"
    path.write_text("this is = not toml ]")
    with pytest.raises(ConfigError):
        load_toml(path)


def test_app_config_scopes(tmp_path):
    cfg = AppConfig.from_file(_write(tmp_path, SAMPLE))
    assert cfg.scope("datasource", "alpha_vantage") == {"api_key": "abc123", "timeout": 10}
    assert cfg.scope("datasource", "missing") == {}


def test_default_sequence_from_top_level_key(tmp_path):
    cfg = AppConfig.from_file(_write(tmp_path, SAMPLE))
    assert cfg.default_sequence() == "main"
    assert cfg.sequence_names() == ["from_cli", "from_env", "main"]


def test_get_sequence_missing_raises(tmp_path):
    cfg = AppConfig.from_file(_write(tmp_path, SAMPLE))
    with pytest.raises(SequenceError):
        cfg.get_sequence("nope")


def test_select_sequence_precedence_cli_over_env_over_config(tmp_path, monkeypatch):
    cfg = AppConfig.from_file(_write(tmp_path, SAMPLE))
    monkeypatch.setenv(ENV_SEQUENCE, "from_env")
    name, data = cfg.select_sequence("from_cli")
    assert name == "from_cli"


def test_select_sequence_env_when_no_cli(tmp_path, monkeypatch):
    cfg = AppConfig.from_file(_write(tmp_path, SAMPLE))
    monkeypatch.setenv(ENV_SEQUENCE, "from_env")
    name, data = cfg.select_sequence(None)
    assert name == "from_env"


def test_select_sequence_config_when_no_cli_or_env(tmp_path, monkeypatch):
    cfg = AppConfig.from_file(_write(tmp_path, SAMPLE))
    monkeypatch.delenv(ENV_SEQUENCE, raising=False)
    name, data = cfg.select_sequence(None)
    assert name == "main"


def test_select_sequence_raises_when_unset(tmp_path, monkeypatch):
    cfg = AppConfig.from_file(_write(tmp_path, "extra = 1\n"))
    monkeypatch.delenv(ENV_SEQUENCE, raising=False)
    with pytest.raises(ConfigError):
        cfg.select_sequence(None)


def test_logging_options_merge_defaults(tmp_path):
    cfg = AppConfig.from_file(_write(tmp_path, SAMPLE))
    opts = cfg.logging_options()
    assert opts["level"] == "DEBUG"
    assert opts["console"] is False
    assert opts["log_file"] is None
    plain = AppConfig({"logging": {}})
    assert plain.logging_options()["level"] == "INFO"
    assert plain.logging_options()["console"] is True

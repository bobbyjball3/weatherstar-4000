"""Tests for the CLI (generate-config + validate run)."""

from weatherstar.cli import main

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 backport
    import tomli as tomllib


CFG = """
sequence = "demo"
[location]
lat = 28.5383
lon = -81.3792
[sequences.demo]
pause = 0.001
slides = [{ screen = "progress" }]
"""


def test_generate_config_outputs_parseable_toml(capsys):
    code = main(["generate-config", "--sequence", "night"])
    assert code == 0
    text = capsys.readouterr().out
    data = tomllib.loads(text)
    assert data["sequence"] == "night"


def test_generate_config_writes_file(tmp_path):
    out = tmp_path / "out.toml"
    code = main(["generate-config", "-o", str(out)])
    assert code == 0
    assert tomllib.loads(out.read_text())["sequence"] == "main"


def test_validate_run_progress(tmp_path, pygame_env, capsys):
    path = tmp_path / "config.toml"
    path.write_text(CFG)
    code = main(
        [
            "--config",
            str(path),
            "--validate",
            "--no-console",
            "--log-level",
            "WARNING",
        ]
    )
    assert code == 0
    assert "OK" in capsys.readouterr().out


def test_missing_config_file_returns_error(capsys):
    code = main(["--config", "/nonexistent/config.toml", "--validate"])
    assert code == 2

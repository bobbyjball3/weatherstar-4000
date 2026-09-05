"""Tests for skeleton config generation."""

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # Python 3.10 backport
    import tomli as tomllib

from weatherstar_4000.v2.config import ConfigValue
from weatherstar_4000.v2.plugin import Plugin
from weatherstar_4000.v2.registry import registry
from weatherstar_4000.v2.skeleton import render_skeleton

# Guard: never pollute the real registry between runs.
_BASE_REGISTRY = {k: dict(v) for k, v in registry._plugins.items()}


def _reg(kind, name, module="tests.v2.test_skeleton", **configs):
    attrs = {"kind": kind, "name": name, "__module__": module, **configs}
    cls = type(name, (Plugin,), attrs)
    registry.register(kind, name, cls)
    return cls


def _restore():
    registry._plugins.clear()
    registry._plugins.update({k: dict(v) for k, v in _BASE_REGISTRY.items()})


def test_render_skeleton_contains_sections_and_parses():
    _reg("screen", "current_conditions", header_text=ConfigValue(default="Now"))
    _reg("screen", "radar", refresh=ConfigValue(default=300, type=int))
    _reg("datasource", "noaa", user_agent=ConfigValue(default="WeatherStar4000/1.0"))
    _reg(
        "datasource",
        "alpha_vantage",
        api_key=ConfigValue(required=True, sensitive=True),
    )
    try:
        text = render_skeleton(sequence_name="night", screen_names=["current_conditions", "radar"])
        data = tomllib.loads(text)
        assert data["sequence"] == "night"
        seq = data["sequences"]["night"]
        assert seq["pause"] == 15.0
        assert {"screen": "current_conditions"} in seq["slides"]
        assert data["screen"]["current_conditions"]["header_text"] == "Now"
        assert data["screen"]["radar"]["refresh"] == 300
        assert "REQUIRED" in text
        # Required, sensitive key is rendered as a commented-out example.
        assert "[datasource.alpha_vantage]" in text
        assert data["datasource"]["alpha_vantage"] == {}
    finally:
        _restore()


def test_render_skeleton_defaults_to_all_registered_screens():
    _reg("screen", "conditions")
    _reg("screen", "radar")
    try:
        text = render_skeleton()
        data = tomllib.loads(text)
        slides = {s["screen"] for s in data["sequences"]["main"]["slides"]}
        assert slides == {"conditions", "radar"}
    finally:
        _restore()


def test_skeleton_logging_block_defaults():
    text = render_skeleton()
    data = tomllib.loads(text)
    assert data["logging"]["level"] == "INFO"
    assert data["logging"]["console"] is True

"""Tests for the plugin registry and discovery."""

import pytest

from weatherstar import PluginNotFound
from weatherstar.plugin import Plugin
from weatherstar.registry import PluginRegistry, plugin, registry


def _mk(kind, name, module=__name__):
    return type(name, (Plugin,), {"kind": kind, "name": name, "__module__": module})


def test_register_and_get_roundtrip():
    reg = PluginRegistry()
    cls = _mk("widget", "alpha")
    reg.register("widget", "alpha", cls)
    assert reg.get("widget", "alpha") is cls
    assert reg.names("widget") == ["alpha"]


def test_register_requires_kind_and_name():
    reg = PluginRegistry()
    with pytest.raises(ValueError):
        reg.register("", "x", _mk("widget", "x"))
    with pytest.raises(ValueError):
        reg.register("widget", "", _mk("widget", "x"))


def test_get_missing_raises_with_available():
    reg = PluginRegistry()
    reg.register("widget", "alpha", _mk("widget", "alpha"))
    reg.register("widget", "beta", _mk("widget", "beta"))
    with pytest.raises(PluginNotFound) as excinfo:
        reg.get("widget", "gamma")
    message = str(excinfo.value)
    assert "gamma" in message
    assert "alpha" in message
    assert "beta" in message


def test_plugin_decorator_registers_by_kind_name():
    class Demo(Plugin):
        kind = "demo"
        name = "sparkle"

    plugin(Demo)
    try:
        assert registry.get("demo", "sparkle") is Demo
    finally:
        registry._plugins.get("demo", {}).pop("sparkle", None)


def test_items_sorted_by_name():
    reg = PluginRegistry()
    reg.register("widget", "zeta", _mk("widget", "zeta"))
    reg.register("widget", "alpha", _mk("widget", "alpha"))
    names = [name for name, _cls in reg.items("widget")]
    assert names == ["alpha", "zeta"]


def test_kinds_lists_kinds():
    reg = PluginRegistry()
    reg.register("aa", "x", _mk("aa", "x"))
    reg.register("bb", "y", _mk("bb", "y"))
    assert reg.kinds() == ["aa", "bb"]


def test_load_builtins_is_idempotent():
    from weatherstar.registry import load_builtins

    load_builtins()
    load_builtins()

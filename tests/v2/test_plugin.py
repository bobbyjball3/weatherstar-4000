"""Tests for the Plugin base: config collection, binding, repr masking."""

import pytest

from weatherstar_4000.v2 import InvalidConfiguration
from weatherstar_4000.v2.plugin import Plugin


def _make_cls(**defaults):
    attrs = {"kind": "widget", "name": "sample", "__module__": __name__}
    attrs.update(defaults)
    return type("Widget", (Plugin,), attrs)


def test_config_spec_collects_descriptors():
    from weatherstar_4000.v2.config import ConfigValue

    cls = _make_cls(
        timeout=ConfigValue(default=10),
        retries=ConfigValue(default=0),
    )
    assert set(cls.config_spec) == {"timeout", "retries"}


def test_inherited_config_spec_merged():
    from weatherstar_4000.v2.config import ConfigValue

    base = _make_cls(timeout=ConfigValue(default=10))
    child = type("FancyWidget", (base,), {"__module__": __name__})
    assert set(child.config_spec) == {"timeout"}


def test_apply_config_merges_defaults():
    from weatherstar_4000.v2.config import ConfigValue

    cls = _make_cls(timeout=ConfigValue(default=10), mode=ConfigValue(default="a"))
    instance = cls()
    instance.apply_config({"mode": "b"})
    assert instance.timeout == 10
    assert instance.mode == "b"


def test_apply_config_required_missing_raises_with_example():
    from weatherstar_4000.v2.config import ConfigValue

    cls = _make_cls(api_key=ConfigValue(required=True, sensitive=True))
    instance = cls()
    with pytest.raises(InvalidConfiguration) as excinfo:
        instance.apply_config({})
    message = str(excinfo.value)
    assert "widget.sample" in message
    assert "api_key" in message
    assert "[widget.sample]" in message
    assert "api_key = " in message  # example snippet present


def test_default_config_includes_required_placeholder():
    from weatherstar_4000.v2.config import ConfigValue

    cls = _make_cls(
        a=ConfigValue(default=3),
        b=ConfigValue(required=True),
    )
    defaults = cls.default_config()
    assert defaults["a"] == 3
    assert defaults["b"] == "<required>"
    assert cls.required_keys() == ("b",)


def test_config_scope_builds_kind_dot_name():
    from weatherstar_4000.v2.config import ConfigValue

    cls = _make_cls(a=ConfigValue(default=1))
    assert cls.config_scope() == "widget.sample"


def test_repr_masks_sensitive_values():
    from weatherstar_4000.v2.config import ConfigValue

    cls = _make_cls(
        api_key=ConfigValue(default="topsecret", sensitive=True),
        label=ConfigValue(default="hello"),
    )
    instance = cls()
    instance.apply_config({})
    text = repr(instance)
    assert "topsecret" not in text
    assert "***" in text
    assert "hello" in text


def test_str_is_safe_for_sensitive():
    from weatherstar_4000.v2.config import ConfigValue

    cls = _make_cls(token=ConfigValue(default="hunter2", sensitive=True))
    instance = cls()
    instance.apply_config({})
    assert "hunter2" not in str(instance)

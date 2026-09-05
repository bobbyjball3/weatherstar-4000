"""Tests for the ConfigValue descriptor and Sensitive masking."""

from weatherstar_4000.v2 import MISSING
from weatherstar_4000.v2.config import ConfigValue, Sensitive, coerce_value


class ConfigHolder:
    timeout = ConfigValue(default=10, type=int)
    retries = ConfigValue(default=0, type=int)
    api_key = ConfigValue(required=True, sensitive=True)
    header = ConfigValue(default="x", sensitive=False)


def test_default_value_returned_when_unset():
    holder = ConfigHolder()
    assert holder.timeout == 10


def test_assigned_value_overrides_default():
    holder = ConfigHolder()
    holder.timeout = 30
    assert holder.timeout == 30


def test_type_coercion_from_string():
    holder = ConfigHolder()
    holder.retries = "5"
    assert holder.retries == 5
    assert isinstance(holder.retries, int)


def test_bool_coercion_from_string():
    class B:
        flag = ConfigValue(default=False, type=bool)

    b = B()
    b.flag = "true"
    assert b.flag is True
    b.flag = "0"
    assert b.flag is False


def test_missing_sentinel_default():
    holder = ConfigHolder()
    assert holder.api_key is MISSING


def test_sensitive_value_masked_in_repr_and_str():
    holder = ConfigHolder()
    holder.api_key = "supersecret"
    value = holder.api_key
    assert isinstance(value, Sensitive)
    assert "supersecret" not in repr(value)
    assert "supersecret" not in str(value)
    assert repr(value) == "***"


def test_sensitive_unwrap_returns_raw_value():
    holder = ConfigHolder()
    holder.api_key = "supersecret"
    assert holder.api_key.unwrap() == "supersecret"
    assert holder.api_key.value == "supersecret"


def test_sensitive_auto_detected_by_key_name():
    assert ConfigValue().is_sensitive is False

    class Auto:
        token = ConfigValue()
        api_key = ConfigValue()
        friendly = ConfigValue()

    descriptors = {k: v for k, v in vars(Auto).items() if isinstance(v, ConfigValue)}
    assert descriptors["token"].is_sensitive is True
    assert descriptors["api_key"].is_sensitive is True
    assert descriptors["friendly"].is_sensitive is False


def test_sensitive_bool_and_equality():
    holder = ConfigHolder()
    holder.api_key = ""
    assert not holder.api_key
    holder.api_key = "abc"
    assert holder.api_key
    assert holder.api_key == "abc"


def test_describe_includes_default_and_required():
    timeout = ConfigHolder.__dict__["timeout"]
    api_key = ConfigHolder.__dict__["api_key"]
    assert "default=10" in timeout.describe()
    assert "required" in api_key.describe()
    assert "sensitive" in api_key.describe()


def test_coerce_value_passthrough_when_no_type():
    assert coerce_value("abc", None) == "abc"
    assert coerce_value(MISSING, int) is MISSING

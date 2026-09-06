"""Tests for Pydantic-based config field behaviour (defaults, coercion, secrets)."""

import pytest
from pydantic import BaseModel, SecretStr, ValidationError

from weatherstar.logging_setup import is_sensitive_key


class ConfigHolder(BaseModel):
    timeout: int = 10
    retries: int = 0
    api_key: SecretStr
    header: str = "x"


def test_default_value_returned_when_unset():
    holder = ConfigHolder(api_key="k")
    assert holder.timeout == 10


def test_assigned_value_overrides_default():
    holder = ConfigHolder(api_key="k")
    holder.timeout = 30
    assert holder.timeout == 30


def test_type_coercion_from_string():
    holder = ConfigHolder(api_key="k", retries="5")
    assert holder.retries == 5
    assert isinstance(holder.retries, int)


def test_bool_coercion_from_string():
    class B(BaseModel):
        flag: bool = False

    assert B(flag="true").flag is True
    assert B(flag="0").flag is False


def test_required_field_missing_raises():
    with pytest.raises(ValidationError):
        ConfigHolder()


def test_sensitive_value_masked_in_repr_and_str():
    holder = ConfigHolder(api_key="supersecret")
    value = holder.api_key
    assert isinstance(value, SecretStr)
    assert "supersecret" not in repr(value)
    assert "supersecret" not in str(value)


def test_sensitive_unwrap_returns_raw_value():
    holder = ConfigHolder(api_key="supersecret")
    assert holder.api_key.get_secret_value() == "supersecret"


def test_sensitive_key_detected_by_name():
    assert is_sensitive_key("api_key") is True
    assert is_sensitive_key("token") is True
    assert is_sensitive_key("password") is True
    assert is_sensitive_key("friendly") is False
    assert is_sensitive_key("timeout") is False


def test_secret_bool_and_equality():
    assert bool(ConfigHolder(api_key="").api_key) is False
    assert bool(ConfigHolder(api_key="abc").api_key) is True
    assert ConfigHolder(api_key="abc").api_key.get_secret_value() == "abc"


def test_extra_keys_ignored():
    holder = ConfigHolder(api_key="k", surprise="value")
    assert holder.timeout == 10

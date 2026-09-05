"""Datasource abstraction: configurable, optionally authenticated data access.

Concrete datasources fetch from external APIs (NOAA, Open Meteo, USGS, Alpha
Vantage, Google News RSS, ...).  Authentication-related :class:`ConfigValue`
fields are declared ``sensitive=True`` and are therefore masked by ``repr`` /
``str`` / the logging redaction processor.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from weatherstar_4000.v2.config import ConfigValue, Sensitive
from weatherstar_4000.v2.logging_setup import get_logger
from weatherstar_4000.v2.plugin import Plugin


class Datasource(Plugin):
    """Base class for plugin datasources.

    Subclasses override their config via :class:`ConfigValue` descriptors and
    implement typed fetch methods.  A thin :meth:`http_get_json` helper centralizes
    logging, header injection and error handling.
    """

    kind = "datasource"

    # Optional common config: each datasource may override defaults.
    timeout = ConfigValue(default=10, type=int)
    user_agent = ConfigValue(default="WeatherStar4000/v2 (python)", type=str)

    # Cache helpers available to subclasses.
    def __init__(self, cache_ttl: int = 300):
        self.cache: dict[str, Any] = {}
        self.cache_time: dict[str, float] = {}
        self.cache_ttl = cache_ttl
        self._session: requests.Session | None = None
        self._log = get_logger("weatherstar4000.v2.datasource")

    # -- HTTP plumbing ------------------------------------------------------

    def _session_for(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            user_agent = self.user_agent
            self._session.headers.update({"User-Agent": user_agent})
            self._apply_auth(self._session)
        return self._session

    def _apply_auth(self, session: requests.Session) -> None:
        """Attach auth derived from sensitive config fields.

        Overridable.  Supported schemes: a ``headers`` mapping, a ``token``
        (sent as ``Authorization: Bearer``), a username/password (basic auth),
        or an ``api_key`` either in a named ``api_key_header`` or as a per-request
        ``api_key_param`` (defaults to the ``X-API-Key`` header).
        """
        spec = type(self).config_spec

        def get(name: str) -> Any:
            if name not in spec:
                return None
            value = getattr(self, name, None)
            if isinstance(value, Sensitive):
                value = value.unwrap()
            return value

        if "headers" in spec and get("headers"):
            session.headers.update(get("headers"))

        token = get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})

        username, password = get("username"), get("password")
        if username is not None and password is not None:
            session.auth = (username, password)

        # Query-param style keys are injected per-request in _query_params.
        if "api_key" in spec and get("api_key") and not get("api_key_param"):
            header_name = get("api_key_header") or "X-API-Key"
            session.headers.update({header_name: get("api_key")})

    def _query_params(self, params: dict[str, Any] | None) -> dict[str, Any] | None:
        spec = type(self).config_spec
        if "api_key_param" not in spec or "api_key" not in spec:
            return params
        param_name = getattr(self, "api_key_param", None)
        api_key = getattr(self, "api_key", None)
        if not param_name or not api_key:
            return params
        if isinstance(api_key, Sensitive):
            api_key = api_key.unwrap()
        merged = dict(params or {})
        merged[param_name] = api_key
        return merged

    def http_get_json(
        self, url: str, params: dict[str, Any] | None = None, timeout: int | None = None
    ) -> dict | list | None:
        """GET ``url`` returning decoded JSON or None on any failure."""
        session = self._session_for()
        resolved_params = self._query_params(params)
        try:
            response = session.get(url, params=resolved_params, timeout=timeout or self.timeout)
            self._log.debug("http_get", url=url, status=response.status_code)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            self._log.warning("http_get_failed", url=url, error=str(exc))
            return None

    # -- Simple TTL cache -----------------------------------------------------

    def _cache_key(self, *parts: Any) -> str:
        import json

        return json.dumps(parts, sort_keys=True, default=str)

    def cache_get(self, key: str, max_age: int | None = None) -> Any | None:
        ttl = max_age if max_age is not None else self.cache_ttl
        if key in self.cache_time and time.time() - self.cache_time[key] < ttl:
            return self.cache.get(key)
        return None

    def cache_set(self, key: str, data: Any) -> None:
        self.cache[key] = data
        self.cache_time[key] = time.time()

    # -- lifecycle -----------------------------------------------------------

    def close(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

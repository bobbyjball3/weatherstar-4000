"""Tests for structured logging setup (colors, sinks, redaction)."""

import io
import logging

from pydantic import SecretStr

from weatherstar_4000 import logging_setup


def _render_via_console(event_dict, colors=True):
    import structlog

    fmt = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=colors),
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            logging_setup.redact_sensitive,
        ],
    )
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(fmt)
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=event_dict.get("event", ""),
        args=(),
        exc_info=None,
    )
    handler.handle(record)
    handler.flush()
    return stream.getvalue()


def test_console_renderer_emits_ansi_colors_by_severity():
    out = _render_via_console({"event": "hello", "level": "info", "levelno": 20})
    assert "\x1b[" in out


def test_console_renderer_can_disable_colors():
    out = _render_via_console({"event": "hello", "level": "info", "levelno": 20}, colors=False)
    assert "\x1b[" not in out


def test_redact_processor_masks_sensitive_keys_and_values():
    event = {
        "event": "calling api",
        "url": "https://api.example.com/v1",
        "headers": {"Authorization": "Bearer abc", "X-Key": "secret-value"},
        "api_key": SecretStr("k"),
        "token": "raw-token",
        "status": 200,
    }
    cleaned = logging_setup.redact_sensitive(None, None, dict(event))
    assert cleaned["api_key"] == "***"
    assert cleaned["token"] == "***"
    assert cleaned["headers"]["Authorization"] == "***"
    assert cleaned["url"] == event["url"]
    assert cleaned["status"] == 200
    assert logging_setup.is_sensitive_key("api_key")
    assert not logging_setup.is_sensitive_key("url")


def test_redact_processor_handles_sensitive_values():
    cleaned = logging_setup.redact_sensitive(None, None, {"secret_obj": SecretStr("v")})
    assert cleaned["secret_obj"] == "***"


def test_setup_logging_writes_json_file_and_console(capsys, tmp_path):
    import structlog

    log_file = tmp_path / "logs.jsonl"
    base = logging_setup.setup_logging(logging.INFO, console=True, log_file=log_file, reset=True)
    base.handlers  # noqa: B018
    structlog.get_logger("weatherstar4000").info("booted", component="engine")
    assert log_file.exists()
    content = log_file.read_text()
    assert "booted" in content


def test_setup_logging_console_disabled_writes_no_stdout(capsys, tmp_path):
    import structlog

    log_file = tmp_path / "only.jsonl"
    logging_setup.setup_logging(logging.INFO, console=False, log_file=log_file, reset=True)
    structlog.get_logger("weatherstar4000").info("quiet", component="engine")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert "quiet" in log_file.read_text()


def test_setup_logging_stamps_timestamp_on_console_and_file(capsys, tmp_path):
    import json
    import re

    import structlog

    log_file = tmp_path / "logs.jsonl"
    logging_setup.setup_logging(logging.INFO, console=True, log_file=log_file, reset=True)
    structlog.get_logger("weatherstar4000").info("booted", component="engine")

    # RFC 3339 timestamp + local alpha TZ abbreviation, e.g.
    # "2026-09-05T10:41:00-04:00 EDT" -> console starts with the year.
    captured = capsys.readouterr()
    console_line = captured.out.splitlines()[0]
    assert console_line.startswith("20")

    record = json.loads(log_file.read_text().splitlines()[0])
    assert record.get("event") == "booted"
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2} \w+", record.get("timestamp", "")
    )

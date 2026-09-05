"""Tests for structured logging setup (colors, sinks, redaction)."""

import io
import logging

from weatherstar_4000.v2 import Sensitive, logging_setup


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
    from weatherstar_4000.v2.config import is_sensitive_key

    event = {
        "event": "calling api",
        "url": "https://api.example.com/v1",
        "headers": {"Authorization": "Bearer abc", "X-Key": "secret-value"},
        "api_key": Sensitive("k"),
        "token": "raw-token",
        "status": 200,
    }
    cleaned = logging_setup.redact_sensitive(None, None, dict(event))
    assert cleaned["api_key"] == "***"
    assert cleaned["token"] == "***"
    assert cleaned["headers"]["Authorization"] == "***"
    assert cleaned["url"] == event["url"]
    assert cleaned["status"] == 200
    assert is_sensitive_key("api_key")
    assert not is_sensitive_key("url")


def test_redact_processor_handles_sensitive_values():
    cleaned = logging_setup.redact_sensitive(None, None, {"secret_obj": Sensitive("v")})
    assert cleaned["secret_obj"] == "***"


def test_setup_logging_writes_json_file_and_console(capsys, tmp_path):
    import structlog

    log_file = tmp_path / "logs.jsonl"
    base = logging_setup.setup_logging(logging.INFO, console=True, log_file=log_file, reset=True)
    base.handlers  # noqa: B018
    structlog.get_logger("weatherstar4000.v2").info("booted", component="engine")
    assert log_file.exists()
    content = log_file.read_text()
    assert "booted" in content


def test_setup_logging_console_disabled_writes_no_stdout(capsys, tmp_path):
    import structlog

    log_file = tmp_path / "only.jsonl"
    logging_setup.setup_logging(logging.INFO, console=False, log_file=log_file, reset=True)
    structlog.get_logger("weatherstar4000.v2").info("quiet", component="engine")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert "quiet" in log_file.read_text()

import logging

import pytest

from src.utils.observability import get_logger, log_stage


def test_log_stage_records_success(caplog):
    logger = get_logger("test.pipeline.success")

    with caplog.at_level(logging.INFO, logger="test.pipeline.success"):
        with log_stage(logger, "silver_transform"):
            pass

    assert "event=stage_started stage=silver_transform" in caplog.text
    assert "event=stage_completed stage=silver_transform" in caplog.text
    assert "duration_seconds=" in caplog.text


def test_log_stage_records_failure_and_reraises(caplog):
    logger = get_logger("test.pipeline.failure")

    with caplog.at_level(logging.ERROR, logger="test.pipeline.failure"):
        with pytest.raises(RuntimeError, match="simulated failure"):
            with log_stage(logger, "gold_build"):
                raise RuntimeError("simulated failure")

    assert "event=stage_failed stage=gold_build" in caplog.text
    assert "simulated failure" in caplog.text

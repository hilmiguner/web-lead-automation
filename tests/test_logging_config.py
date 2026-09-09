import logging

from web_lead_automation.logging_config import configure_logging, get_logger


def test_configure_logging_sets_root_level():
    configure_logging("DEBUG")

    assert logging.getLogger().level == logging.DEBUG


def test_get_logger_returns_named_logger():
    logger = get_logger("web_lead_automation.test")

    assert logger.name == "web_lead_automation.test"

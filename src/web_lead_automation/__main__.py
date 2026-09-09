"""Minimal application entry point used during foundation development."""

from web_lead_automation.config import get_settings
from web_lead_automation.logging_config import configure_logging, get_logger


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    logger.info("Web Lead Automation initialized in %s mode.", settings.app_env)


if __name__ == "__main__":
    main()

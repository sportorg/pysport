import logging

logger = logging.getLogger(__name__)


def log_rust_status() -> None:
    try:
        from sportorg_rust_example import status_message
    except ModuleNotFoundError as exc:
        return

    logger.info(status_message())

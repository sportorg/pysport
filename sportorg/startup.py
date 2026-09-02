"""Startup sequence.

``sportorg.config`` and ``sportorg.paths`` are deliberately free of
import-time side effects, so something has to create the directories and
configure logging explicitly.  That is this module, and the order matters:
logging cannot open its files before ``logs/`` exists, and seeding has to
finish before anything can write ``settings.json`` and erase the first-run
signal.
"""

import logging
import logging.config
import os

from sportorg import config, paths
from sportorg.paths import PathsError

__all__ = ["PathsError", "configure_logging", "init"]


def configure_logging() -> None:
    logging.config.dictConfig(config.build_log_config())


def init() -> None:
    """Prepare the filesystem, then logging, then the seeded directories."""
    paths.ensure_dirs()
    if config.TEMPLATES_PATH:
        os.makedirs(config.TEMPLATES_PATH, exist_ok=True)

    configure_logging()
    if paths.should_seed():
        paths.seed_if_first_run()

"""Filesystem roots for SportOrg.

Every path is derived from the program itself, never from the working
directory:

* ``package_dir()`` — read-only resources shipped inside ``sportorg.data``
* ``app_dir()`` — the directory holding the executable (or the repository
  root when running from source)
* ``data_dir()`` / ``log_dir()`` — user-writable state under ``app_dir()``

Importing this module has no side effects.  Creating the directories and
seeding them from the package is the job of :func:`sportorg.startup.init`.
"""

import atexit
import logging
import os
import shutil
import sys
from contextlib import ExitStack
from typing import Dict, Tuple

try:
    from importlib.resources import as_file, files
except ImportError:
    from importlib_resources import as_file, files

# Directories that exist both inside the package and under ``data/``: the
# package copy is the reference, the ``data/`` copy is what the user edits.
SEEDED = ("configs", "templates", "sounds")

logger = logging.getLogger(__name__)


class PathsError(Exception):
    """A directory SportOrg needs to write to could not be created."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__("{}: {}".format(path, reason))
        self.path = path
        self.reason = reason


def is_executable() -> bool:
    return hasattr(sys, "frozen")


def app_dir(*parts: str) -> str:
    """The directory the program lives in.

    Frozen builds resolve next to the executable; source checkouts resolve to
    the repository root, which is the parent of the ``sportorg`` package.
    """
    if is_executable():
        root = os.path.dirname(sys.executable)
    else:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    return os.path.join(root, *parts)


_RESOURCE_STACK = ExitStack()
atexit.register(_RESOURCE_STACK.close)
_RESOURCE_PATH_CACHE: Dict[Tuple[str, ...], str] = {}
_RESOURCE_ROOT = files("sportorg.data")


def package_dir(*parts: str) -> str:
    """A read-only resource shipped inside the ``sportorg.data`` package."""
    key = tuple(parts)
    if key not in _RESOURCE_PATH_CACHE:
        resource = _RESOURCE_ROOT.joinpath(*parts)
        _RESOURCE_PATH_CACHE[key] = str(
            _RESOURCE_STACK.enter_context(as_file(resource))
        )

    return _RESOURCE_PATH_CACHE[key]


def data_dir(*parts: str) -> str:
    return app_dir("data", *parts)


def log_dir(*parts: str) -> str:
    return app_dir("logs", *parts)


def settings_json() -> str:
    return data_dir("settings.json")


def resolve_seeded(name: str, *parts: str, override: str = "") -> str:
    """Resolve a seeded directory through override, ``data/`` and package.

    The package tier is load-bearing: seeding only happens on a first run, so
    an upgraded installation can reach this function before ``data/<name>/``
    exists.  Falling through to the package keeps the application usable
    instead of raising on a missing directory.
    """
    if override:
        return os.path.join(override, *parts)

    root = data_dir(name)
    if not os.path.isdir(root):
        root = package_dir(name)

    return os.path.join(root, *parts)


def should_seed() -> bool:
    """Whether ``data/`` should be filled from the package on a first run.

    Only frozen builds seed.  A source checkout reads the package copies
    directly: copying them into ``data/`` would shadow the files under
    ``sportorg/data/``, so editing a template or a reference table in the
    repository would silently stop having any effect.
    """
    return is_executable()


def ensure_dirs() -> None:
    """Create the writable roots, or explain why that is impossible."""
    for path in (data_dir(), log_dir()):
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            raise PathsError(path, str(e)) from e


def seed_if_first_run() -> None:
    """Copy the package defaults into ``data/`` on a first run.

    A directory is seeded only when neither ``settings.json`` nor the target
    directory exists, so an existing installation is never overwritten.  Each
    directory is judged on its own, and a failure to copy one of them is
    logged rather than raised: the caller can still fall back to the package.
    """
    settings_exists = os.path.exists(settings_json())
    for name in SEEDED:
        target = data_dir(name)
        if settings_exists or os.path.isdir(target):
            continue

        try:
            source = package_dir(name)
        except Exception:
            logger.exception("Package directory %s is unavailable", name)
            continue

        if not os.path.isdir(source):
            logger.error("Package directory %s is missing at %s", name, source)
            continue

        try:
            shutil.copytree(source, target)
        except OSError:
            logger.exception("Failed to copy %s to %s", source, target)
            continue

        logger.info("Copied %s to %s", source, target)

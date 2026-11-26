# ruff: noqa: INP001 - standalone script, not part of a package
"""
Check that the integration imports cleanly on a Home Assistant release.

Copyright (c) 2026 Jeffrey C Honig. MIT License, see LICENSE.

Usage:
    ha_compat_check.py resolve {minimum,latest,beta}
        Print the Home Assistant version to test for a CI target:
        minimum is the "homeassistant" key in hacs.json, latest is the
        newest stable release on PyPI, and beta is the newest release
        including pre-releases.

    ha_compat_check.py check
        Import every module of the integration with the installed Home
        Assistant. Fail on any import error, and on any warning that
        mentions the integration (such as a Home Assistant deprecation
        notice) unless it matches a line in ha_deprecations_allowed.txt.
"""

from __future__ import annotations

import importlib
import json
import logging
import pkgutil
import sys
import urllib.request
import warnings
from pathlib import Path

from packaging.version import Version

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "custom_components.cyberq"
ALLOWED_FILE = Path(__file__).resolve().parent / "ha_deprecations_allowed.txt"
PYPI_URL = "https://pypi.org/pypi/homeassistant/json"


def resolve(target: str) -> str:
    """Return the Home Assistant version to test for a CI target."""
    if target == "minimum":
        return json.loads((ROOT / "hacs.json").read_text())["homeassistant"]
    with urllib.request.urlopen(PYPI_URL, timeout=30) as response:
        data = json.load(response)
    if target == "latest":
        return data["info"]["version"]
    if target == "beta":
        versions = [
            Version(version)
            for version, files in data["releases"].items()
            if files and not all(file.get("yanked") for file in files)
        ]
        return str(max(versions))
    msg = f"unknown target {target!r}"
    raise ValueError(msg)


class _Collector(logging.Handler):
    """Collect log records that mention the integration."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if "cyberq" in message or record.name.startswith(PACKAGE):
            self.messages.append(message)


def _allowed_patterns() -> list[str]:
    lines = ALLOWED_FILE.read_text().splitlines()
    return [line for line in lines if line.strip() and not line.startswith("#")]


def check() -> int:
    """Import every module of the integration and report problems."""
    import homeassistant.const  # noqa: PLC0415 - installed per CI target

    sys.path.insert(0, str(ROOT))
    collector = _Collector()
    logging.getLogger().addHandler(collector)
    logging.captureWarnings(capture=True)
    warnings.simplefilter("always")

    out = sys.stdout
    out.write(f"Home Assistant {homeassistant.const.__version__}\n")
    failed = False
    package = importlib.import_module(PACKAGE)
    for module in pkgutil.iter_modules(package.__path__):
        name = f"{PACKAGE}.{module.name}"
        try:
            importlib.import_module(name)
        except Exception as err:  # noqa: BLE001 - report every failure
            out.write(f"::error::import {name} failed: {err!r}\n")
            failed = True
        else:
            out.write(f"ok {name}\n")

    allowed = _allowed_patterns()
    for message in collector.messages:
        if any(pattern in message for pattern in allowed):
            out.write(f"::warning::known deprecation: {message}\n")
        else:
            out.write(f"::error::unexpected warning: {message}\n")
            failed = True
    return 1 if failed else 0


def main() -> int:
    """Run the requested command."""
    match sys.argv[1:]:
        case ["resolve", target]:
            sys.stdout.write(resolve(target) + "\n")
            return 0
        case ["check"]:
            return check()
    sys.stderr.write(__doc__ or "")
    return 2


if __name__ == "__main__":
    sys.exit(main())

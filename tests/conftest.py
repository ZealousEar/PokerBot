"""Pytest setup — put the project root on sys.path so tests can do
`from src.bot import decide` and friends.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FULLHOUSE_ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
FULLHOUSE_ENGINE_AVAILABLE = (FULLHOUSE_ENGINE_DIR / "sandbox" / "runner.py").is_file()
FULLHOUSE_ENGINE_SKIP_REASON = "requires ext/fullhouse-engine sandbox runner"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_engine: requires the external ext/fullhouse-engine checkout",
    )


def pytest_collection_modifyitems(config, items):
    if FULLHOUSE_ENGINE_AVAILABLE:
        return
    skip_engine = pytest.mark.skip(reason=FULLHOUSE_ENGINE_SKIP_REASON)
    for item in items:
        if "requires_engine" in item.keywords:
            item.add_marker(skip_engine)

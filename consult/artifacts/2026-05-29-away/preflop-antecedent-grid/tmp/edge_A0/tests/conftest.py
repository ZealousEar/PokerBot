"""Pytest setup — put the project root on sys.path so tests can do
`from src.bot import decide` and friends.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

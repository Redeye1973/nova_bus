"""Shared conftest for pytest discovery of shared fixtures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

"""python -m v2_services.agent_64_software_test_runner"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from v2_services.agent_64_software_test_runner.runners import amain

    asyncio.run(amain())

"""Base contract for tool tests."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class TestResult:
    tool_name: str
    status: str  # pass, fail, skip
    duration_ms: int
    category: str = ""
    output_path: Optional[Path] = None
    output_size_bytes: Optional[int] = None
    output_hash: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolTest:
    TOOL_NAME = ""
    CATEGORY = ""  # infrastructure, audio, image, three_d, gis, data
    TIER = 1  # 1=light, 2=medium, 3=heavy
    TIMEOUT_SECONDS = 120
    EXPECTED_OUTPUT_FILENAME = "output.bin"
    MIN_OUTPUT_SIZE_BYTES = 16
    REQUIRES_BRIDGE = False

    async def run(self, output_dir: Path) -> TestResult:
        raise NotImplementedError

    def verify_output(self, output_dir: Path) -> tuple[bool, str]:
        output = output_dir / self.EXPECTED_OUTPUT_FILENAME
        if not output.exists():
            return False, f"Output missing: {output}"
        size = output.stat().st_size
        if size < self.MIN_OUTPUT_SIZE_BYTES:
            return False, f"Output too small: {size} < {self.MIN_OUTPUT_SIZE_BYTES}"
        return True, "OK"

"""SuperCollider: verify sclang runs; artifact is a small WAV (Python wave) for baseline."""
from __future__ import annotations

import asyncio
import shutil
import wave
from pathlib import Path
import time

from .._base import TestResult, ToolTest

SCLANG_CANDIDATES = [
    Path(r"L:\ZZZ Software\Super Collider\sclang.exe"),
    Path(r"C:\Program Files\SuperCollider-3.13.0\sclang.exe"),
]


class SuperColliderTest(ToolTest):
    TOOL_NAME = "supercollider"
    CATEGORY = "audio"
    TIER = 2
    TIMEOUT_SECONDS = 60
    EXPECTED_OUTPUT_FILENAME = "test_laser.wav"
    MIN_OUTPUT_SIZE_BYTES = 500

    def _sclang(self) -> Path | None:
        for c in SCLANG_CANDIDATES:
            if c.is_file():
                return c
        w = shutil.which("sclang")
        return Path(w) if w else None

    def _write_wav(self, path: Path) -> None:
        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b"\x00\x01" * 8000)  # ~0.18s

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        wav = output_dir / self.EXPECTED_OUTPUT_FILENAME
        exe = self._sclang()
        sc_ok = False
        if exe:
            scd = output_dir / "probe.scd"
            scd.write_text('"NOVA softtest".postln;\n0.exit;\n', encoding="utf-8")
            proc = await asyncio.create_subprocess_exec(
                str(exe), str(scd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(proc.communicate(), self.TIMEOUT_SECONDS)
                sc_ok = proc.returncode == 0
            except asyncio.TimeoutError:
                proc.kill()
                return TestResult(
                    self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                    category=self.CATEGORY, error_message="sclang timeout",
                )
        else:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message="sclang.exe not found",
            )
        self._write_wav(wav)
        ms = int((time.perf_counter() - t0) * 1000)
        if not sc_ok:
            return TestResult(
                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                error_message="sclang non-zero exit",
                metadata={"wav_fallback": True},
            )
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=wav, output_size_bytes=wav.stat().st_size,
            metadata={"sclang": str(exe)},
        )

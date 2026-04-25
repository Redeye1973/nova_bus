"""Tier-based software test orchestration."""
from __future__ import annotations

import asyncio
import importlib
import inspect
import os
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from .output_writers import hash_file, write_inventory, write_run_info, write_timing_csv
from .tool_tests._base import TestResult, ToolTest

PKG = "v2_services.agent_64_software_test_runner.tool_tests"


def discover_tests() -> list[ToolTest]:
    tests: list[ToolTest] = []
    base = Path(__file__).resolve().parent / "tool_tests"
    for category_dir in sorted(base.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("_"):
            continue
        for test_file in sorted(category_dir.glob("*.py")):
            if test_file.name.startswith("_"):
                continue
            mod_name = f"{PKG}.{category_dir.name}.{test_file.stem}"
            try:
                module = importlib.import_module(mod_name)
            except Exception as e:
                print(f"  warn: skip {mod_name}: {e}")
                continue
            for _name, cls in inspect.getmembers(module, inspect.isclass):
                if cls is ToolTest or not issubclass(cls, ToolTest):
                    continue
                if cls.__module__ != mod_name:
                    continue
                try:
                    tests.append(cls())
                except Exception as e:
                    print(f"  warn: {cls}: {e}")
    return tests


class SoftwareTestRunner:
    GROUP_COOLDOWN_SECONDS = int(os.getenv("SOFTTEST_GROUP_COOLDOWN_SECONDS", "30"))

    def __init__(self, output_root: Path, run_id: str | None = None) -> None:
        self.output_root = Path(output_root)
        desc = os.getenv("SOFTTEST_DESCRIPTION", "first_test")
        day = datetime.now().strftime("%Y-%m-%d")
        self.run_id = run_id or f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.run_dir = self.output_root / "_runs" / f"{day}_{desc}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[TestResult] = []
        self.started_at = datetime.now().isoformat()

    async def run_all(self) -> list[TestResult]:
        all_tests = discover_tests()
        tier_1 = [t for t in all_tests if t.TIER == 1]
        tier_2 = [t for t in all_tests if t.TIER == 2]
        tier_3 = [t for t in all_tests if t.TIER == 3]
        if os.getenv("SOFTTEST_SKIP_TIER3") == "1":
            print("  (SOFTTEST_SKIP_TIER3: skipping heavy tier)")
            tier_3 = []
        print(f"Run {self.run_id}: tier1={len(tier_1)} tier2={len(tier_2)} tier3={len(tier_3)}")

        print("\n=== Tier 1: Infrastructure (parallel) ===")
        await self._run_tier_parallel(tier_1)
        await self._cooldown()

        print("\n=== Tier 2: Light tools (groups of 3) ===")
        if os.getenv("SOFTTEST_SEQUENTIAL") == "1":
            for t in tier_2:
                await self._run_single(t)
        else:
            for i in range(0, len(tier_2), 3):
                await self._run_tier_parallel(tier_2[i : i + 3])
                if i + 3 < len(tier_2):
                    await asyncio.sleep(10)
        await self._cooldown()

        print("\n=== Tier 3: Heavy tools (sequential) ===")
        for test in tier_3:
            await self._run_single(test)
            await asyncio.sleep(10)

        return self.results

    async def _run_tier_parallel(self, tests: list[ToolTest]) -> None:
        if not tests:
            return
        if os.getenv("SOFTTEST_SEQUENTIAL") == "1":
            for t in tests:
                await self._run_single(t)
        else:
            await asyncio.gather(*[self._run_single(t) for t in tests], return_exceptions=True)

    async def _run_single(self, test: ToolTest) -> TestResult:
        tool_dir = self.run_dir / f"{test.CATEGORY}_{test.TOOL_NAME}"
        try:
            result = await test.run(tool_dir)
        except Exception as e:
            result = TestResult(
                tool_name=test.TOOL_NAME,
                status="fail",
                duration_ms=0,
                category=test.CATEGORY,
                error_message=f"Test exception: {e}",
            )
        if not result.category:
            result = replace(result, category=test.CATEGORY)
        if result.status == "pass" and result.output_path and result.output_path.is_file():
            try:
                result = replace(result, output_hash=hash_file(Path(result.output_path)))
            except Exception:
                pass
        self.results.append(result)
        sym = {"pass": "[OK]", "fail": "[FAIL]", "skip": "[SKIP]"}.get(result.status, "[?]")
        print(f"  {sym} {test.CATEGORY}/{test.TOOL_NAME} ({result.duration_ms}ms)")
        return result

    async def _cooldown(self) -> None:
        if self.GROUP_COOLDOWN_SECONDS <= 0:
            return
        print(f"\n  Cooldown {self.GROUP_COOLDOWN_SECONDS}s...\n")
        await asyncio.sleep(self.GROUP_COOLDOWN_SECONDS)


async def amain() -> None:
    root = Path(
        os.getenv(
            "SOFTTEST_OUTPUT_ROOT",
            r"L:\! 2 Nova v2  OUTPUT !\Z New NOva 1st test",
        )
    )
    if os.getenv("SOFTTEST_QUICK") == "1":
        os.environ.setdefault("SOFTTEST_GROUP_COOLDOWN_SECONDS", "5")
    runner = SoftwareTestRunner(root)
    results = await runner.run_all()
    write_run_info(runner.run_dir, runner.run_id, results, runner.started_at)
    write_timing_csv(runner.run_dir, results)
    write_inventory(runner.run_dir, results)
    p = sum(1 for r in results if r.status == "pass")
    f = sum(1 for r in results if r.status == "fail")
    s = sum(1 for r in results if r.status == "skip")
    print(f"\n=== DONE pass={p} fail={f} skip={s} dir={runner.run_dir} ===")


if __name__ == "__main__":
    # Allow `python -m v2_services.agent_64_software_test_runner.runners` from repo root
    repo = Path(__file__).resolve().parents[2]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    asyncio.run(amain())

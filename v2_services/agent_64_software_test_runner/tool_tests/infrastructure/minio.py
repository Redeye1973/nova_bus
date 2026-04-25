"""MinIO: put/get round-trip of health-only check (geen credentials)."""
from __future__ import annotations

import time
import uuid
from pathlib import Path

import httpx

from .._base import TestResult, ToolTest
from .._env import MINIO_ACCESS, MINIO_SECRET, MINIO_URL


class MinioTest(ToolTest):
    TOOL_NAME = "minio"
    CATEGORY = "infrastructure"
    TIER = 1
    EXPECTED_OUTPUT_FILENAME = "downloaded.txt"

    async def run(self, output_dir: Path) -> TestResult:
        t0 = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / self.EXPECTED_OUTPUT_FILENAME
        if not MINIO_ACCESS or not MINIO_SECRET:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    base = MINIO_URL.rstrip("/")
                    r = await client.get(f"{base}/minio/health/ready")
                    if r.status_code == 200:
                        out.write_text("minio_health_ready\n", encoding="utf-8")
                        ms = int((time.perf_counter() - t0) * 1000)
                        ok, reason = self.verify_output(output_dir)
                        if not ok:
                            return TestResult(
                                self.TOOL_NAME, "fail", ms, category=self.CATEGORY,
                                error_message=reason,
                            )
                        return TestResult(
                            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
                            output_path=out, output_size_bytes=out.stat().st_size,
                            metadata={"check": "health_only"},
                        )
            except Exception as e:
                return TestResult(
                    self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                    category=self.CATEGORY,
                    error_message=f"MINIO credentials ontbreken; health check faalde: {e}",
                )
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="MINIO_ROOT_USER / MINIO_ROOT_PASSWORD not set en health niet OK",
            )
        bucket = "software-test-probe"
        key = f"probe/{uuid.uuid4().hex}.txt"
        body = b"nova software test object\n"
        try:
            from minio import Minio
            from minio.error import S3Error

            endpoint = MINIO_URL.replace("http://", "").replace("https://", "")
            secure = MINIO_URL.startswith("https://")
            client = Minio(endpoint, access_key=MINIO_ACCESS, secret_key=MINIO_SECRET, secure=secure)
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
            from io import BytesIO

            client.put_object(bucket, key, BytesIO(body), length=len(body), content_type="text/plain")
            obj = client.get_object(bucket, key)
            data = obj.read()
            obj.close()
            obj.release_conn()
            if data != body:
                return TestResult(
                    self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                    category=self.CATEGORY, error_message="round-trip bytes mismatch",
                )
            client.remove_object(bucket, key)
            out.write_bytes(data)
        except ImportError:
            return TestResult(
                self.TOOL_NAME, "skip", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY,
                error_message="minio package not installed (pip install minio)",
            )
        except S3Error as e:
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message=str(e),
            )
        except Exception as e:
            return TestResult(
                self.TOOL_NAME, "fail", int((time.perf_counter() - t0) * 1000),
                category=self.CATEGORY, error_message=str(e),
            )
        ms = int((time.perf_counter() - t0) * 1000)
        ok, reason = self.verify_output(output_dir)
        if not ok:
            return TestResult(self.TOOL_NAME, "fail", ms, category=self.CATEGORY, error_message=reason)
        return TestResult(
            self.TOOL_NAME, "pass", ms, category=self.CATEGORY,
            output_path=out, output_size_bytes=out.stat().st_size,
            metadata={"bucket": bucket, "key": key},
        )

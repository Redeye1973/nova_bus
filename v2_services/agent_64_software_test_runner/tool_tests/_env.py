"""Shared URLs and env for software tests."""
from __future__ import annotations

import os

PUBLIC_HOST = os.getenv("SOFTTEST_PUBLIC_HOST", "178.104.207.194")

QDRANT_URL = os.getenv("SOFTTEST_QDRANT_URL", f"http://{PUBLIC_HOST}:6333")
MINIO_URL = os.getenv("SOFTTEST_MINIO_URL", f"http://{PUBLIC_HOST}:19000")
N8N_URL = os.getenv("SOFTTEST_N8N_URL", f"http://{PUBLIC_HOST}:5679")
OLLAMA_URL = os.getenv("SOFTTEST_OLLAMA_URL", "http://127.0.0.1:11434")

MEMORY_CURATOR_URL = os.getenv("SOFTTEST_MEMORY_URL", f"http://{PUBLIC_HOST}:8060")

MINIO_ACCESS = os.getenv("MINIO_ROOT_USER") or os.getenv("SOFTTEST_MINIO_USER", "")
MINIO_SECRET = os.getenv("MINIO_ROOT_PASSWORD") or os.getenv("SOFTTEST_MINIO_PASSWORD", "")

"""H15: Shared test fixtures for NOVA v2 agents.

Usage in any agent's conftest.py:
    from shared.test_fixtures import client_factory, sample_payloads
"""
from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def agent_client(request) -> Generator[TestClient, None, None]:
    """Generic fixture that creates a TestClient for any agent's FastAPI app.

    Usage: mark the test module with the agent's main module path.

    Example:
        @pytest.fixture
        def client():
            from main import app
            return TestClient(app)
    """
    from main import app
    with TestClient(app) as client:
        yield client


SAMPLE_PAYLOADS: Dict[str, Dict[str, Any]] = {
    "cost_record": {
        "service": "openai",
        "operation": "gpt-4-turbo",
        "estimated_cost_eur": 0.03,
        "actual_cost_eur": 0.025,
        "agent_id": "agent_12",
    },
    "error_report": {
        "service": "agent_14_blender",
        "severity": "high",
        "message": "blender.exe returned exit code 1: CUDA out of memory",
        "stack_trace": "subprocess.CalledProcessError: ...",
    },
    "prompt_feedback": {
        "prompt_name": "build_v2_agent",
        "version": 2,
        "success": True,
        "judge_verdict": "pass",
        "latency_ms": 4500,
        "cost_usd": 0.08,
    },
    "memory_store": {
        "agent_id": "agent_12",
        "content": "Successfully baked tile 1234AB with 4 layers",
        "tags": ["bake", "success", "1234AB"],
        "importance": 0.7,
    },
    "pipeline_start": {
        "name": "bake_1234AB",
        "triggered_by": "n8n_workflow_42",
    },
    "asset_register": {
        "name": "tile_1234AB_bag.gml",
        "asset_type": "gml",
        "source": "pdok_bag",
        "job_id": "test-job-1",
        "agent_id": "agent_13",
    },
}


def assert_health_ok(client: TestClient) -> Dict[str, Any]:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    return data


def assert_invoke_error(client: TestClient, action: str, expected_in_response: str = "error") -> Dict[str, Any]:
    r = client.post("/invoke", json={"action": action})
    data = r.json()
    assert expected_in_response in str(data).lower() or "valid" in str(data).lower()
    return data

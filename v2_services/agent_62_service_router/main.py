"""NOVA Service Router — multi-provider fallback chains for LLM, image, and audio."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import deque
import httpx
import os
import time
import logging

logger = logging.getLogger("service_router")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="NOVA Service Router", version="1.0")

VAULT_URL = os.getenv("VAULT_URL", "http://nova-v2-agent-44-secrets-vault:8144")
VAULT_TOKEN = os.getenv("NOVA_VAULT_TOKEN", "")
NOTIFICATION_HUB_URL = os.getenv("NOTIFICATION_HUB_URL", "http://nova-v2-notification-hub:8061")

_call_log: deque = deque(maxlen=500)
_failure_counts: Dict[str, int] = {}


async def _get_secret(name: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {VAULT_TOKEN}"} if VAULT_TOKEN else {}
            r = await client.post(f"{VAULT_URL}/secrets/get", json={"name": name}, headers=headers, timeout=5)
            if r.status_code == 200:
                return r.json().get("value")
    except Exception:
        pass
    return os.getenv(name)


LLM_CHAINS = [
    {"provider": "anthropic", "model": "claude-sonnet-4-6", "api_key_name": "ANTHROPIC_API_KEY",
     "url": "https://api.anthropic.com/v1/messages"},
    {"provider": "openai", "model": "gpt-4-turbo", "api_key_name": "OPENAI_API_KEY",
     "url": "https://api.openai.com/v1/chat/completions"},
]

IMAGE_CHAINS = [
    {"provider": "meshy", "api_key_name": "MESHY_API_KEY", "url": "https://api.meshy.ai"},
    {"provider": "comfyui_local", "url": "http://comfyui:8188"},
]

AUDIO_CHAINS = [
    {"provider": "audiocraft_local", "url": "http://audiocraft:8080"},
    {"provider": "elevenlabs", "api_key_name": "ELEVENLABS_API_KEY",
     "url": "https://api.elevenlabs.io/v1"},
]


class CompletionRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7
    prefer_provider: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


async def _call_anthropic(provider: dict, req: CompletionRequest, api_key: str) -> Dict[str, Any]:
    messages = [{"role": "user", "content": req.prompt}]
    body: Dict[str, Any] = {
        "model": provider["model"], "max_tokens": req.max_tokens,
        "temperature": req.temperature, "messages": messages,
    }
    if req.system:
        body["system"] = req.system
    async with httpx.AsyncClient() as client:
        r = await client.post(provider["url"], json=body, headers={
            "x-api-key": api_key, "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }, timeout=60)
        r.raise_for_status()
        data = r.json()
        return {"text": data["content"][0]["text"], "provider": "anthropic",
                "model": provider["model"], "usage": data.get("usage", {})}


async def _call_openai(provider: dict, req: CompletionRequest, api_key: str) -> Dict[str, Any]:
    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.prompt})
    async with httpx.AsyncClient() as client:
        r = await client.post(provider["url"], json={
            "model": provider["model"], "max_tokens": req.max_tokens,
            "temperature": req.temperature, "messages": messages,
        }, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=60)
        r.raise_for_status()
        data = r.json()
        return {"text": data["choices"][0]["message"]["content"], "provider": "openai",
                "model": provider["model"], "usage": data.get("usage", {})}


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "chains": {"llm": len(LLM_CHAINS), "image": len(IMAGE_CHAINS), "audio": len(AUDIO_CHAINS)},
            "total_calls": len(_call_log)}


@app.get("/health/deep")
async def health_deep() -> Dict[str, Any]:
    import shutil
    anthropic_key = bool(await _get_secret("ANTHROPIC_API_KEY"))
    openai_key = bool(await _get_secret("OPENAI_API_KEY"))
    try:
        disk = f"{shutil.disk_usage('/').free / 1e9:.1f}GB free"
    except Exception:
        disk = "unknown"
    return {
        "overall": "healthy" if (anthropic_key or openai_key) else "degraded",
        "service": "ok", "agent": "62_service_router", "version": "1.0",
        "providers": {"anthropic": anthropic_key, "openai": openai_key},
        "failure_counts": dict(_failure_counts),
        "disk_space": disk,
    }


@app.post("/llm/complete")
async def llm_complete(req: CompletionRequest) -> Dict[str, Any]:
    chain = LLM_CHAINS.copy()
    if req.prefer_provider:
        chain.sort(key=lambda p: 0 if p["provider"] == req.prefer_provider else 1)

    errors = []
    for provider in chain:
        api_key = await _get_secret(provider.get("api_key_name", ""))
        if not api_key and provider.get("api_key_name"):
            errors.append({"provider": provider["provider"], "error": "no_api_key"})
            continue

        started = time.time()
        try:
            if provider["provider"] == "anthropic":
                result = await _call_anthropic(provider, req, api_key)
            elif provider["provider"] == "openai":
                result = await _call_openai(provider, req, api_key)
            else:
                continue

            elapsed = time.time() - started
            _call_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": "llm", "provider": provider["provider"],
                "model": provider.get("model"), "elapsed_s": round(elapsed, 2),
                "success": True,
            })
            return result

        except Exception as e:
            elapsed = time.time() - started
            _failure_counts[provider["provider"]] = _failure_counts.get(provider["provider"], 0) + 1
            errors.append({"provider": provider["provider"], "error": str(e), "elapsed_s": round(elapsed, 2)})
            _call_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": "llm", "provider": provider["provider"],
                "elapsed_s": round(elapsed, 2), "success": False, "error": str(e),
            })
            logger.warning(f"Provider {provider['provider']} failed: {e}")

    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{NOTIFICATION_HUB_URL}/notify", json={
                "severity": "critical", "title": "All LLM providers failed",
                "detail": str(errors), "source": "agent_62_service_router",
            }, timeout=5)
    except Exception:
        pass

    raise HTTPException(503, detail={"error": "all_providers_failed", "attempts": errors})


@app.get("/providers")
async def list_providers() -> Dict[str, Any]:
    return {
        "llm": [{"provider": p["provider"], "model": p.get("model")} for p in LLM_CHAINS],
        "image": [{"provider": p["provider"]} for p in IMAGE_CHAINS],
        "audio": [{"provider": p["provider"]} for p in AUDIO_CHAINS],
    }


@app.get("/stats")
async def call_stats(limit: int = 50) -> Dict[str, Any]:
    return {"total_calls": len(_call_log), "failures": dict(_failure_counts),
            "recent": list(_call_log)[-limit:]}


@app.post("/invoke")
async def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    action = body.get("action", "")
    if action == "complete":
        return await llm_complete(CompletionRequest(**body))
    elif action == "providers":
        return await list_providers()
    elif action == "stats":
        return await call_stats(body.get("limit", 50))
    else:
        raise HTTPException(400, f"Unknown action: {action}")

"""Session 03: V1 workflow inventory + capabilities JSON (no stdout of secrets)."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"L:/!Nova V2")
SECRETS = ROOT / "secrets" / "nova_v2_passwords.txt"
BRIEF = ROOT / "briefings"


def _v1_key() -> str:
    text = SECRETS.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^N8N_V1_API_KEY=(.+)$", text, re.MULTILINE)
    if not m:
        sys.exit("missing N8N_V1_API_KEY")
    return m.group(1).strip().strip('"').strip("'")


def _webhook_paths(nodes: list) -> list[str]:
    paths: list[str] = []
    for n in nodes or []:
        if not isinstance(n, dict):
            continue
        t = (n.get("type") or "").lower()
        if "webhook" not in t:
            continue
        params = n.get("parameters") or {}
        p = params.get("path")
        if isinstance(p, str) and p.strip():
            paths.append(p.strip())
    return sorted(set(paths))


def _fetch_workflows(key: str) -> list[dict]:
    url = "http://178.104.207.194:5678/api/v1/workflows?limit=100"
    req = urllib.request.Request(url, headers={"X-N8N-API-KEY": key})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.load(r)
    return list(data.get("data") or [])


def _keyword_score(name: str, paths: list[str]) -> int:
    blob = (name + " " + " ".join(paths)).lower()
    keys = (
        "code",
        "scaffold",
        "fastapi",
        "pytest",
        "docker",
        "orchestr",
        "deploy",
        "codegen",
        "generator",
        "build",
        "nova",
        "cursor",
        "python",
        "test",
    )
    return sum(1 for k in keys if k in blob)


def main() -> None:
    key = _v1_key()
    workflows = _fetch_workflows(key)
    total = len(workflows)
    active_wfs = [w for w in workflows if w.get("active")]

    inv_rows: list[dict] = []
    build_hits: list[dict] = []

    for w in workflows:
        wid = w.get("id")
        name = w.get("name") or ""
        active = bool(w.get("active"))
        nodes = w.get("nodes") or []
        paths = _webhook_paths(nodes)
        row = {
            "id": wid,
            "name": name,
            "active": active,
            "webhook_paths": paths,
        }
        inv_rows.append(row)
        if _keyword_score(name, paths) >= 2 or any(
            x in " ".join(paths).lower() for x in ("orchestr", "build", "nova", "code")
        ):
            build_hits.append({"id": wid, "name": name, "active": active, "webhook_paths": paths})

    inventory = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "active": len(active_wfs),
        "workflows": inv_rows,
    }
    BRIEF.mkdir(parents=True, exist_ok=True)
    (BRIEF / "v1_workflow_inventory.json").write_text(
        json.dumps(inventory, indent=2), encoding="utf-8"
    )

    orchestrator_paths = sorted(
        {p for w in inv_rows for p in w["webhook_paths"] if "orchestr" in p.lower() or p.lower() in ("nova-orchestrator", "nova_v2_build_task", "nova_v2_build")}
    )

    codegen_test = {"status": "not_attempted", "detail": ""}
    test_urls = [
        "http://178.104.207.194:5678/webhook/nova-orchestrator",
        "http://178.104.207.194:5678/webhook/nova_v2_build_task",
    ]
    payload = json.dumps(
        {
            "task_type": "capability_check",
            "prompt": "Generate a Python function that adds two integers.",
            "language": "python",
        }
    ).encode("utf-8")

    for attempt, url in enumerate(test_urls, start=1):
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-N8N-API-KEY": key,
                "X-Task-Source": "cursor_session_03",
                "X-Task-Priority": "normal",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8", errors="replace")[:4000]
            codegen_test = {
                "status": "http_ok",
                "url": url,
                "http_status": r.status,
                "response_snippet_chars": len(body),
            }
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500] if e.fp else ""
            codegen_test = {
                "status": "http_error",
                "url": url,
                "http_status": e.code,
                "attempt": attempt,
                "body_preview_chars": len(body),
            }
            if attempt >= 2:
                break
        except OSError as e:
            codegen_test = {
                "status": "network_error",
                "url": url,
                "error": type(e).__name__,
                "attempt": attempt,
            }
            if attempt >= 2:
                break

    caps = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "v1_workflow_total": total,
        "v1_workflow_active": len(active_wfs),
        "build_related_workflows": build_hits[:40],
        "orchestrator_like_paths_found": orchestrator_paths,
        "codegen_probe": codegen_test,
        "notes": "Delegation endpoints in repo docs: /webhook/nova-orchestrator (unified) vs /webhook/nova_v2_build_task (mega_plan). Probe uses both; interpret http_ok as reachable webhook, not necessarily codegen success.",
    }
    if codegen_test.get("status") not in ("http_ok",):
        caps["codegen"] = "fallback_to_cursor"
        caps["codegen_reason"] = "webhook probe did not complete with success semantics; use V1 UI to confirm orchestrator path and payload contract."

    (BRIEF / "v1_capabilities.json").write_text(json.dumps(caps, indent=2), encoding="utf-8")
    print("wrote", BRIEF / "v1_workflow_inventory.json")
    print("wrote", BRIEF / "v1_capabilities.json")
    print("build_hits", len(build_hits))


if __name__ == "__main__":
    main()

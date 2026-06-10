#!/usr/bin/env python3
"""FASE 10 — Agent vlootcheck: 3-laags inventaris (draait / antwoordt / werkt)."""
from __future__ import annotations

import base64
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(r"L:\!Nova V2")
OUT_RAW = REPO / "docs" / "fase10_vloot_raw.json"
HETZNER = os.getenv("NOVA_PUBLIC_HOST", "178.104.207.194")
SSH = ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", f"root@{HETZNER}"]

# 1x1 transparent PNG for sprite jury pixel-check
_MINI_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

LOCAL_AGENTS: List[Dict[str, Any]] = [
    {
        "id": "orchestrator",
        "name": "orchestrator_nova1",
        "port": 8000,
        "health_path": "/status",
        "runtime": "host",
        "in_canonical": True,
        "kind": "orchestrator",
    },
    {"id": "sprite_jury", "name": "sprite_jury_v2", "port": 8101, "runtime": "docker", "in_canonical": True, "kind": "jury"},
    {"id": "monitor", "name": "agent_11_monitor", "port": 8111, "runtime": "docker", "in_canonical": True, "kind": "monitor"},
    {"id": "cost_guard", "name": "agent_16_cost_guard", "port": 8116, "runtime": "docker", "in_canonical": True},
    {"id": "elevenlabs", "name": "agent_29_elevenlabs", "port": 8129, "runtime": "docker", "in_canonical": True},
    {"id": "parallax_36", "name": "agent_36_parallax_jury", "port": 8136, "runtime": "docker", "in_canonical": True, "kind": "jury_local"},
    {"id": "art_dir_37", "name": "agent_37_art_director", "port": 8137, "runtime": "docker", "in_canonical": True, "kind": "meta_judge"},
    {"id": "quality_38", "name": "agent_38_quality_inspector", "port": 8138, "runtime": "docker", "in_canonical": True, "kind": "inspector"},
    {"id": "audio_dir_39", "name": "agent_39_audio_director", "port": 8139, "runtime": "docker", "in_canonical": True, "kind": "audio_director"},
    {"id": "juice_40", "name": "agent_40_juice_inspector", "port": 8140, "runtime": "docker", "in_canonical": True, "kind": "inspector"},
    {"id": "resume_41", "name": "agent_41_resume_agent", "port": 8141, "runtime": "host", "in_canonical": True, "kind": "resume"},
    {"id": "parts_42", "name": "agent_42_parts_planner", "port": 8142, "runtime": "host", "in_canonical": True, "kind": "planner"},
    {"id": "dale", "name": "dale_factory_worker", "port": 8170, "runtime": "host", "in_canonical": True},
    {"id": "hybrid_gate", "name": "hybrid_gate", "port": 8191, "runtime": "host", "in_canonical": True},
    {"id": "bridge_8500", "name": "host_bridge", "port": 8500, "runtime": "host", "in_canonical": True, "kind": "bridge"},
    {"id": "bridge_8501", "name": "host_bridge_legacy", "port": 8501, "runtime": "host", "in_canonical": False, "kind": "bridge_legacy"},
    {"id": "audiocraft", "name": "audiocraft", "port": 8080, "runtime": "docker", "in_canonical": True},
    {"id": "judge_local", "name": "nova-judge", "port": None, "container": "nova-v2-judge", "internal_port": 8000, "runtime": "docker_internal", "in_canonical": False, "kind": "judge"},
    {"id": "vault_local", "name": "agent_44_secrets_vault", "port": None, "container": "nova-v2-agent-44-secrets-vault", "internal_port": 8144, "runtime": "docker_internal", "in_canonical": False},
]

HETZNER_JURY = list(range(1, 11)) + [24, 30]
HETZNER_AGENTS: List[Dict[str, Any]] = []
for n in range(1, 36):
    if n == 34:
        continue  # no agent 34 in Hetzner list
    port = 8100 + n
    kind = "jury" if n in HETZNER_JURY else "service"
    if n == 11:
        kind = "monitor"
    if n == 13:
        kind = "pdok"
    if n in (14, 22):
        kind = "blender"
    if n == 21:
        kind = "freecad"
    container = f"nova-v2-agent-{n:02d}" if n < 10 else f"nova-v2-agent-{n}"
    if n == 2:
        container = "nova-v2-agent-02"
    elif n >= 10:
        # naming varies — resolved at runtime from docker ps
        container = None
    HETZNER_AGENTS.append(
        {
            "id": f"hetzner_{n:02d}",
            "num": n,
            "port": port,
            "kind": kind,
            "container_hint": container,
            "in_canonical": False,
            "archived_local": n in (2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 24, 30),
        }
    )
HETZNER_AGENTS.append({"id": "hetzner_judge", "num": 0, "port": 8000, "kind": "judge", "container_hint": "nova-v2-judge", "in_canonical": False})
HETZNER_AGENTS.append({"id": "hetzner_monitor", "num": 11, "port": 8111, "kind": "monitor", "container_hint": "nova-v2-agent-11-monitor", "in_canonical": True, "archived_local": False})


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def http_req(
    method: str,
    url: str,
    body: Optional[dict] = None,
    raw_body: Optional[bytes] = None,
    headers: Optional[dict] = None,
    timeout: float = 5.0,
) -> Tuple[int, Any, float, str]:
    t0 = time.perf_counter()
    hdrs = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    if raw_body is not None:
        data = raw_body
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    err = ""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ms = round((time.perf_counter() - t0) * 1000, 1)
            try:
                return resp.status, json.loads(raw.decode("utf-8")), ms, ""
            except json.JSONDecodeError:
                return resp.status, raw[:500].decode("utf-8", errors="replace"), ms, ""
    except urllib.error.HTTPError as e:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw) if raw.strip() else {}, ms, raw[:300]
        except json.JSONDecodeError:
            return e.code, raw[:300], ms, raw[:300]
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return -1, {}, ms, f"{type(exc).__name__}:{exc}"


def layer1_local_port(port: int) -> Tuple[bool, str]:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True, "port_open"
    except OSError as e:
        return False, str(e)


def layer1_docker_container(name: str) -> Tuple[bool, str]:
    try:
        r = subprocess.run(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        line = (r.stdout or "").strip()
        if line and "Up" in line:
            return True, line
        return False, line or "not_running"
    except Exception as e:
        return False, str(e)


def hetzner_ssh(cmd: str, timeout: float = 30.0) -> Tuple[int, str]:
    try:
        r = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def hetzner_container_map() -> Dict[str, str]:
    code, out = hetzner_ssh("docker ps --format '{{.Names}}'")
    names = [ln.strip() for ln in out.splitlines() if ln.strip()]
    m: Dict[str, str] = {}
    for name in names:
        m[name] = name
        # agent number extraction
        mobj = re.search(r"agent-(\d+)", name)
        if mobj:
            m[f"num_{mobj.group(1)}"] = name
        if "judge" in name:
            m["judge"] = name
        if "sprite-jury" in name:
            m["sprite"] = name
    return m


def hetzner_health(container: str, port: int) -> Tuple[int, Any, float, str]:
    py = (
        "import urllib.request,sys;"
        f"r=urllib.request.urlopen('http://127.0.0.1:{port}/health',timeout=4);"
        "sys.stdout.write(r.read().decode())"
    )
    cmd = f"docker exec {container} python3 -c \"{py}\""
    t0 = time.perf_counter()
    code, out = hetzner_ssh(cmd, timeout=15)
    ms = round((time.perf_counter() - t0) * 1000, 1)
    if code != 0:
        return -1, {}, ms, out.strip()[:300]
    try:
        return 200, json.loads(out), ms, ""
    except json.JSONDecodeError:
        return 200, out[:200], ms, ""


def functional_local(agent: Dict[str, Any]) -> Tuple[bool, str, Any]:
    kind = agent.get("kind", "")
    port = agent.get("port")
    if not port:
        return False, "no_port", None

  # juries / sprite
    if kind == "jury":
        st, data, _, err = http_req(
            "POST",
            f"http://127.0.0.1:{port}/v1/verdict",
            {"pixel_integrity": 8.0, "jury_scores": [8.0, 8.5, 7.5]},
            timeout=8,
        )
        ok = st == 200 and isinstance(data, dict) and "verdict" in data
        return ok, err or f"http_{st}", data

    if kind == "jury_local":
        st, data, _, err = http_req(
            "POST",
            f"http://127.0.0.1:{port}/v1/verdict",
            {"parallax_integrity": 7.5, "jury_scores": [7.0, 8.0]},
            timeout=8,
        )
        ok = st == 200 and isinstance(data, dict) and "verdict" in data
        return ok, err or f"http_{st}", data

    if kind == "monitor":
        st, data, _, err = http_req("GET", f"http://127.0.0.1:{port}/status", timeout=20)
        ok = st == 200 and isinstance(data, dict) and (
            "targets" in data or "results" in data or "targets_checked" in data
        )
        return ok, err or f"http_{st}", data

    if kind == "judge":
        st, data, _, err = http_req(
            "POST",
            "http://127.0.0.1:8000/evaluate",
            {"task_result": {"jury_verdict": "accept", "average_score": 8.0}, "logs": []},
            timeout=8,
        )
        ok = st == 200 and isinstance(data, dict)
        return ok, err or f"http_{st}", data

    if kind == "audio_director":
        with tempfile.TemporaryDirectory(prefix="nova_fase10_") as tmp:
            out_dir = tmp.replace("\\", "/")
            st, data, _, err = http_req(
                "POST",
                f"http://127.0.0.1:{port}/plan",
                {
                    "domain": "shmup",
                    "project": "fase10_smoke",
                    "brief": "mini ambient layer",
                    "output_dir": out_dir,
                },
                timeout=20,
            )
        ok = st == 200 and isinstance(data, dict)
        return ok, err or f"http_{st}", data

    if kind == "meta_judge":
        st, data, _, err = http_req(
            "POST",
            f"http://127.0.0.1:{port}/review",
            {
                "domain": "shmup",
                "asset_paths": [],
                "structure_data": {"enemy_types": ["a", "b", "c"], "spawn_waves": [{"enemy_count": 2}]},
                "project": "fase10_smoke",
            },
            timeout=15,
        )
        ok = st == 200 and isinstance(data, dict)
        return ok, err or f"http_{st}", data

    if kind == "inspector":
        st, data, _, err = http_req(
            "POST",
            f"http://127.0.0.1:{port}/inspect",
            {"domain": "shmup", "unit_type": "enemy", "unit_data": {"z_index": 1, "parallax": 0.5}},
            timeout=15,
        )
        ok = st in (200, 422) and isinstance(data, dict)
        return ok, err or f"http_{st}", data

    if kind == "resume":
        st, data, _, err = http_req("GET", f"http://127.0.0.1:{port}/active", timeout=8)
        ok = st == 200
        return ok, err or f"http_{st}", data

    if kind == "planner":
        st, data, _, err = http_req(
            "POST",
            f"http://127.0.0.1:{port}/plan",
            {
                "project_id": "fase10_smoke",
                "project_name": "Fase10 Smoke",
                "domain": "shmup",
                "brief": "Mini smoke: valideer parallax layer en enemy spawn",
                "register": False,
            },
            timeout=90,
        )
        ok = st == 200 and isinstance(data, dict) and "parts" in data
        return ok, err or f"http_{st}", data

    if kind == "bridge":
        st, data, _, err = http_req("GET", f"http://127.0.0.1:{port}/health", timeout=5)
        ok = st == 200
        return ok, err or f"http_{st}", data

    if kind == "bridge_legacy":
        return False, "port_not_listening_expected", None

    if kind == "orchestrator":
        st, data, _, err = http_req("GET", f"http://127.0.0.1:{port}/status", timeout=8)
        ok = st == 200 and isinstance(data, dict) and data.get("ok")
        return ok, err or f"http_{st}", data

    # generic health-only agents
    st, data, _, err = http_req("GET", f"http://127.0.0.1:{port}/health", timeout=5)
    ok = st == 200
    return ok, err or f"http_{st}", data


def functional_hetzner(agent: Dict[str, Any], container: str) -> Tuple[bool, str, Any]:
    kind = agent.get("kind", "")
    port = agent["port"]
    n = agent.get("num", 0)

    if kind == "jury":
        py = (
            "import urllib.request,json,sys;"
            "b=json.dumps({'pixel_integrity':8.0,'jury_scores':[8,8,7]}).encode();"
            f"req=urllib.request.Request('http://127.0.0.1:{port}/v1/verdict',data=b,method='POST',"
            "headers={'Content-Type':'application/json'});"
            "r=urllib.request.urlopen(req,timeout=6);sys.stdout.write(r.read().decode())"
        )
        if n == 1:
            py = (
                "import urllib.request,json,sys;"
                "b=json.dumps({'pixel_integrity':8.0,'jury_scores':[8,8,7]}).encode();"
                f"req=urllib.request.Request('http://127.0.0.1:{port}/v1/verdict',data=b,method='POST',"
                "headers={'Content-Type':'application/json'});"
                "r=urllib.request.urlopen(req,timeout=6);sys.stdout.write(r.read().decode())"
            )
        cmd = f"docker exec {container} python3 -c \"{py}\""
        code, out = hetzner_ssh(cmd, timeout=20)
        if code != 0:
            # fallback unified review for code jury etc
            py2 = (
                "import urllib.request,json,sys;"
                "b=json.dumps({'language':'python','code':'x=1'}).encode();"
                f"req=urllib.request.Request('http://127.0.0.1:{port}/review',data=b,method='POST',"
                "headers={'Content-Type':'application/json'});"
                "r=urllib.request.urlopen(req,timeout=6);sys.stdout.write(r.read().decode())"
            )
            cmd2 = f"docker exec {container} python3 -c \"{py2}\""
            code, out = hetzner_ssh(cmd2, timeout=20)
        try:
            data = json.loads(out)
            ok = "verdict" in data or "average_score" in data or "results" in data
            return ok, "" if ok else "no_verdict_field", data
        except json.JSONDecodeError:
            return False, out[:200], None

    if kind == "pdok":
        py = (
            "import urllib.request,sys;"
            f"r=urllib.request.urlopen('http://127.0.0.1:{port}/jaargangen?gemeente=Amsterdam',timeout=8);"
            "sys.stdout.write(r.read().decode()[:500])"
        )
        cmd = f"docker exec {container} python3 -c \"{py}\""
        code, out = hetzner_ssh(cmd, timeout=20)
        if code != 0:
            py = (
                "import urllib.request,sys;"
                f"r=urllib.request.urlopen('http://127.0.0.1:{port}/years?municipality=Amsterdam',timeout=8);"
                "sys.stdout.write(r.read().decode()[:500])"
            )
            cmd = f"docker exec {container} python3 -c \"{py}\""
            code, out = hetzner_ssh(cmd, timeout=20)
        ok = code == 0 and len(out.strip()) > 2
        return ok, out[:200] if not ok else "", out[:300]

    if kind == "blender":
        py = (
            "import urllib.request,sys;"
            f"r=urllib.request.urlopen('http://127.0.0.1:{port}/version',timeout=10);"
            "sys.stdout.write(r.read().decode()[:300])"
        )
        cmd = f"docker exec {container} python3 -c \"{py}\""
        code, out = hetzner_ssh(cmd, timeout=25)
        if code != 0:
            py = (
                "import urllib.request,sys;"
                f"r=urllib.request.urlopen('http://127.0.0.1:{port}/health',timeout=5);"
                "sys.stdout.write(r.read().decode())"
            )
            cmd = f"docker exec {container} python3 -c \"{py}\""
            code, out = hetzner_ssh(cmd, timeout=15)
        ok = code == 0
        return ok, out[:200] if not ok else "", out[:300]

    if kind == "freecad":
        py = (
            "import urllib.request,json,sys;"
            "b=json.dumps({'category':'box','dimensions':{'x':1,'y':1,'z':1}}).encode();"
            f"req=urllib.request.Request('http://127.0.0.1:{port}/parametric',data=b,method='POST',"
            "headers={'Content-Type':'application/json'});"
            "r=urllib.request.urlopen(req,timeout=15);sys.stdout.write(r.read().decode()[:400])"
        )
        cmd = f"docker exec {container} python3 -c \"{py}\""
        code, out = hetzner_ssh(cmd, timeout=30)
        ok = code == 0
        return ok, out[:200] if not ok else "", out[:300]

    if kind == "monitor":
        py = (
            "import urllib.request,sys;"
            f"r=urllib.request.urlopen('http://127.0.0.1:{port}/status',timeout=12);"
            "sys.stdout.write(r.read().decode()[:800])"
        )
        cmd = f"docker exec {container} python3 -c \"{py}\""
        code, out = hetzner_ssh(cmd, timeout=25)
        ok = code == 0 and "targets" in out
        return ok, out[:200] if not ok else "", out[:400]

    if kind == "judge":
        py = (
            "import urllib.request,json,sys;"
            "b=json.dumps({'task_result':{'jury_verdict':'accept','average_score':8},'logs':[]}).encode();"
            f"req=urllib.request.Request('http://127.0.0.1:{port}/evaluate',data=b,method='POST',"
            "headers={'Content-Type':'application/json'});"
            "r=urllib.request.urlopen(req,timeout=6);sys.stdout.write(r.read().decode())"
        )
        cmd = f"docker exec {container} python3 -c \"{py}\""
        code, out = hetzner_ssh(cmd, timeout=20)
        try:
            data = json.loads(out)
            ok = code == 0 and isinstance(data, dict)
            return ok, out[:200] if not ok else "", data
        except json.JSONDecodeError:
            return False, out[:200], None

    # generic health as functional fallback
    st, data, _, err = hetzner_health(container, port)
    return st == 200, err, data


def classify(l1: bool, l2: bool, l3: bool, in_canonical: bool, running: bool) -> str:
    if running and not in_canonical:
        return "GRIJS"
    if not in_canonical and not running:
        return "GRIJS"
    if l1 and l2 and l3:
        return "GROEN"
    if l1 and l2:
        return "GEEL"
    return "ROOD"


def check_local_agent(agent: Dict[str, Any]) -> Dict[str, Any]:
    rec: Dict[str, Any] = {
        "scope": "local",
        "id": agent["id"],
        "name": agent["name"],
        "in_canonical": agent.get("in_canonical", False),
        "runtime": agent.get("runtime"),
    }
    port = agent.get("port")
    container = agent.get("container")

    if agent.get("runtime") == "docker_internal":
        cname = agent.get("container", "")
        l1, l1d = layer1_docker_container(cname)
        rec["layer1"] = {"ok": l1, "detail": l1d}
        if l1:
            st, data, ms, err = hetzner_health(cname, agent["internal_port"])  # reuse python exec locally
            # local docker exec
            py = (
                "import urllib.request,sys;"
                f"r=urllib.request.urlopen('http://127.0.0.1:{agent['internal_port']}/health',timeout=4);"
                "sys.stdout.write(r.read().decode())"
            )
            r = subprocess.run(
                ["docker", "exec", cname, "python3", "-c", py],
                capture_output=True,
                text=True,
                timeout=15,
            )
            l2 = r.returncode == 0
            ms = 0
            err = r.stderr[:200] if not l2 else ""
            rec["layer2"] = {"ok": l2, "http": 200 if l2 else -1, "ms": ms, "error": err}
            if agent.get("kind") == "judge":
                ip = agent["internal_port"]
                judge_py = (
                    "import urllib.request,json,sys;"
                    "b=json.dumps({'task_result':{'jury_verdict':'accept'},'logs':[]}).encode();"
                    f"req=urllib.request.Request('http://127.0.0.1:{ip}/evaluate',data=b,method='POST',"
                    "headers={'Content-Type':'application/json'});"
                    "r=urllib.request.urlopen(req,timeout=5);sys.stdout.write(r.read().decode())"
                )
                r2 = subprocess.run(
                    ["docker", "exec", cname, "python3", "-c", judge_py],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                l3 = r2.returncode == 0
                rec["layer3"] = {"ok": l3, "detail": r2.stdout[:200] if l3 else r2.stderr[:200]}
            else:
                rec["layer3"] = {"ok": l2, "detail": "health_only"}
        else:
            rec["layer2"] = {"ok": False, "error": "container_down"}
            rec["layer3"] = {"ok": False, "error": "container_down"}
    elif port:
        if agent.get("runtime") == "docker":
            cname = agent["name"].replace("_", "-")
            # try common container naming
            for cand in [
                f"nova-v2-{agent['name'].replace('_', '-')}",
                f"nova-v2-{agent['id'].replace('_', '-')}",
                "nova-v2-sprite-jury" if "sprite" in agent["id"] else "",
            ]:
                if cand and layer1_docker_container(cand)[0]:
                    container = cand
                    break
            l1, l1d = layer1_docker_container(container or agent["name"]) if container else layer1_local_port(port)
            if not container:
                l1, l1d = layer1_local_port(port)
        else:
            l1, l1d = layer1_local_port(port)
        rec["layer1"] = {"ok": l1, "detail": l1d}
        hp = agent.get("health_path", "/health")
        st, data, ms, err = http_req("GET", f"http://127.0.0.1:{port}{hp}", timeout=5)
        l2 = st == 200
        rec["layer2"] = {"ok": l2, "http": st, "ms": ms, "error": err}
        l3, l3d, l3data = functional_local(agent)
        rec["layer3"] = {"ok": l3, "detail": l3d, "sample": str(l3data)[:300] if l3data else None}
    else:
        rec["layer1"] = {"ok": False, "detail": "no_endpoint"}
        rec["layer2"] = {"ok": False}
        rec["layer3"] = {"ok": False}

    rec["classification"] = classify(
        rec["layer1"]["ok"],
        rec["layer2"]["ok"],
        rec["layer3"]["ok"],
        agent.get("in_canonical", False),
        rec["layer1"]["ok"],
    )
    return rec


def check_hetzner_agent(agent: Dict[str, Any], cmap: Dict[str, str]) -> Dict[str, Any]:
    rec: Dict[str, Any] = {
        "scope": "hetzner",
        "id": agent["id"],
        "num": agent.get("num"),
        "port": agent["port"],
        "kind": agent.get("kind"),
        "in_canonical": agent.get("in_canonical", False),
        "archived_local": agent.get("archived_local", False),
    }
    n = agent.get("num")
    container = agent.get("container_hint")
    if n:
        for key in (f"num_{n:02d}", f"num_{n}"):
            if key in cmap:
                container = cmap[key]
                break
    if agent["id"] == "hetzner_judge":
        container = cmap.get("judge", "nova-v2-judge")
    if n == 1:
        container = cmap.get("sprite", "nova-v2-sprite-jury")

    if not container:
        rec["layer1"] = {"ok": False, "detail": "container_not_found"}
        rec["layer2"] = {"ok": False}
        rec["layer3"] = {"ok": False}
        rec["classification"] = "ROOD"
        return rec

    rec["container"] = container
    code, out = hetzner_ssh(f"docker inspect -f '{{{{.State.Status}}}}' {container}", timeout=10)
    l1 = code == 0 and "running" in out.lower()
    rec["layer1"] = {"ok": l1, "detail": out.strip()}

    if l1:
        st, data, ms, err = hetzner_health(container, agent["port"])
        l2 = st == 200
        rec["layer2"] = {"ok": l2, "http": st, "ms": ms, "error": err, "body": str(data)[:200]}
        l3, l3d, l3data = functional_hetzner(agent, container)
        rec["layer3"] = {"ok": l3, "detail": l3d, "sample": str(l3data)[:300] if l3data else None}
    else:
        rec["layer2"] = {"ok": False, "error": "container_not_running"}
        rec["layer3"] = {"ok": False}

    running = l1
    in_can = agent.get("in_canonical", False)
    if running and agent.get("archived_local"):
        rec["classification"] = "GRIJS"
    else:
        rec["classification"] = classify(
            rec["layer1"]["ok"],
            rec["layer2"]["ok"],
            rec["layer3"]["ok"],
            in_can,
            running,
        )
    return rec


def hetzner_resource_snapshot() -> Dict[str, Any]:
    code, out = hetzner_ssh(
        "docker stats --no-stream --format '{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}' 2>/dev/null | grep -E 'agent|judge|sprite' | sort",
        timeout=60,
    )
    rows = []
    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) >= 4:
            rows.append({"name": parts[0], "cpu": parts[1], "mem": parts[2], "mem_pct": parts[3]})
    return {"ok": code == 0, "containers": rows, "raw_lines": len(rows)}


def main() -> int:
    print("=== FASE 10 Vlootcheck ===", now_iso())
    results: Dict[str, Any] = {
        "generated_at": now_iso(),
        "gate": {},
        "local": [],
        "hetzner": [],
        "hetzner_resources": {},
        "summary": {},
    }

    # Gate check
    tags = subprocess.run(["git", "tag", "-l"], capture_output=True, text=True, cwd=REPO)
    tag_list = (tags.stdout or "").splitlines()
    results["gate"]["fase9_tag"] = "fase9-dispatch-compleet" in tag_list
    results["gate"]["fase9_report"] = (REPO / "docs" / "fase9_report.md").is_file()
    results["gate"]["fase9_diagnose"] = (REPO / "docs" / "fase9_diagnose.md").is_file()
    results["gate"]["fase8_evidence"] = (REPO / "docs" / "fase8_evidence" / "regress_a.json").is_file()

    print("Local agents...")
    for agent in LOCAL_AGENTS:
        rec = check_local_agent(agent)
        results["local"].append(rec)
        print(f"  {rec['id']}: {rec['classification']} L1={rec['layer1']['ok']} L2={rec['layer2']['ok']} L3={rec['layer3']['ok']}")

    print("Hetzner agents...")
    cmap = hetzner_container_map()
    results["hetzner_container_map"] = cmap
    for agent in HETZNER_AGENTS:
        if agent["id"] in ("hetzner_monitor",):
            continue  # duplicate of local monitor check on Hetzner
        rec = check_hetzner_agent(agent, cmap)
        results["hetzner"].append(rec)
        print(f"  {rec['id']}: {rec['classification']} L1={rec['layer1']['ok']} L2={rec['layer2']['ok']} L3={rec['layer3']['ok']}")

    results["hetzner_resources"] = hetzner_resource_snapshot()

    all_recs = results["local"] + results["hetzner"]
    groen = sum(1 for r in all_recs if r["classification"] == "GROEN")
    geel = sum(1 for r in all_recs if r["classification"] == "GEEL")
    rood = sum(1 for r in all_recs if r["classification"] == "ROOD")
    grijs = sum(1 for r in all_recs if r["classification"] == "GRIJS")
    results["summary"] = {
        "total": len(all_recs),
        "GROEN": groen,
        "GEEL": geel,
        "ROOD": rood,
        "GRIJS": grijs,
        "local_health_15": sum(
            1
            for r in results["local"]
            if r.get("in_canonical") and r["layer2"]["ok"]
        ),
        "local_canonical_count": sum(1 for a in LOCAL_AGENTS if a.get("in_canonical")),
    }

    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    OUT_RAW.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT_RAW}")
    print(f"Summary: GROEN={groen} GEEL={geel} ROOD={rood} GRIJS={grijs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

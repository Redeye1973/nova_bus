"""NOVA proof-standaard (Fase 2) — make_proof / verify_proof / record_proof.

proof = {
    "type": "file" | "job" | "render" | "report",
    "path": "<canoniek Windows-pad>" (bij file/render),
    "id": "<job_id of rapport-id>" (bij job/report),
    "hash": "sha256:<hex>" (bij files),
    "timestamp": "<UTC ISO>",
    "agent": "<agent-naam>",
}

Zelfde import-patroon als vision_eye.py: agents doen
    sys.path.insert(0, "/nova_shared"); sys.path.insert(0, r"L:\\!Nova V2\\shared")
Pad-vertaling container<->host via env NOVA_PATH_MAP, bv.
    NOVA_PATH_MAP=L:\\ZZZ ZZ NOVA GAME OUTPUT=/game_output;L:\\!Nova V2=/nova_v2
Alleen stdlib — ook bruikbaar door Dale (host-python zonder extra deps).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROOF_TYPES = ("file", "job", "render", "report")

PROOFS_FILE = Path(
    os.getenv("NOVA_PROOFS_FILE") or "L:\\!Nova V2\\status\\nova_proofs.jsonl"
)


def _path_map() -> List[Tuple[str, str]]:
    """Paren 'windows_prefix=local_mount' uit NOVA_PATH_MAP (containers)."""
    raw = os.getenv("NOVA_PATH_MAP", "")
    pairs: List[Tuple[str, str]] = []
    for part in raw.split(";"):
        if "=" in part:
            win, local = part.split("=", 1)
            win = win.strip()
            local = local.strip()
            if win and local:
                pairs.append((win, local))
    return pairs


def to_local_path(path: str) -> Path:
    """Vertaal canoniek Windows-pad naar lokaal (container-)pad indien gemapt."""
    p = (path or "").strip()
    norm = p.replace("/", "\\")
    for win, local in _path_map():
        wprefix = win.replace("/", "\\")
        if norm.lower().startswith(wprefix.lower()):
            rel = norm[len(wprefix):].lstrip("\\/")
            return Path(local) / rel.replace("\\", "/")
    return Path(p)


def to_windows_path(path: str) -> str:
    """Vertaal lokaal (container-)pad terug naar canoniek Windows-pad."""
    p = (path or "").strip()
    posix = p.replace("\\", "/")
    for win, local in _path_map():
        lprefix = local.replace("\\", "/").rstrip("/")
        if posix.lower().startswith(lprefix.lower()):
            rel = posix[len(lprefix):].lstrip("/")
            return win.rstrip("\\/") + ("\\" + rel.replace("/", "\\") if rel else "")
    return p


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def make_proof(
    proof_type: str,
    *,
    path: str = "",
    id: str = "",
    agent: str = "",
    note: str = "",
) -> Dict[str, Any]:
    """Bouw een proof-object; bij file/render met bestaand bestand ook hash."""
    if proof_type not in PROOF_TYPES:
        raise ValueError(f"onbekend proof type: {proof_type}")
    proof: Dict[str, Any] = {
        "type": proof_type,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent": agent or os.getenv("NOVA_AGENT_NAME", "unknown"),
    }
    if path:
        proof["path"] = to_windows_path(path)
    if id:
        proof["id"] = id
    if note:
        proof["note"] = note
    if proof_type in ("file", "render") and path:
        local = to_local_path(proof["path"])
        if local.is_file():
            proof["hash"] = file_hash(local)
    return proof


def verify_proof(proof: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Verifieer een proof-object. ok=False bij structuur-, bestaan- of hash-fout."""
    checks: List[str] = []
    if not isinstance(proof, dict):
        return {"ok": False, "reason": "proof_missing_or_not_dict", "checks": checks}
    ptype = str(proof.get("type") or "")
    if ptype not in PROOF_TYPES:
        return {"ok": False, "reason": f"invalid_type:{ptype or 'leeg'}", "checks": checks}
    checks.append("type_ok")
    if not proof.get("timestamp"):
        return {"ok": False, "reason": "timestamp_missing", "checks": checks}
    checks.append("timestamp_ok")
    if not proof.get("agent"):
        return {"ok": False, "reason": "agent_missing", "checks": checks}
    checks.append("agent_ok")

    if ptype in ("file", "render"):
        path = str(proof.get("path") or "")
        if not path:
            return {"ok": False, "reason": "path_missing", "checks": checks}
        local = to_local_path(path)
        if not local.is_file():
            return {"ok": False, "reason": f"file_not_found:{path}", "checks": checks}
        checks.append("file_exists")
        expected = str(proof.get("hash") or "")
        if not expected:
            return {"ok": False, "reason": "hash_missing_for_file_proof", "checks": checks}
        actual = file_hash(local)
        if actual != expected:
            return {
                "ok": False,
                "reason": "hash_mismatch",
                "expected": expected,
                "actual": actual,
                "checks": checks,
            }
        checks.append("hash_ok")
    else:  # job / report
        if not (proof.get("id") or proof.get("path")):
            return {"ok": False, "reason": "id_or_path_required", "checks": checks}
        checks.append("id_ok")

    return {"ok": True, "checks": checks}


def record_proof(proof: Dict[str, Any], *, context: str = "") -> Dict[str, Any]:
    """Append proof naar nova_proofs.jsonl (registry voor Monitor-steekproef)."""
    entry = dict(proof)
    if context:
        entry["context"] = context
    try:
        PROOFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PROOFS_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=True) + "\n")
        return {"recorded": True, "file": str(PROOFS_FILE)}
    except Exception as exc:  # registry-fout mag agent-response niet breken
        return {"recorded": False, "error": str(exc)}


def make_and_record(
    proof_type: str,
    *,
    path: str = "",
    id: str = "",
    agent: str = "",
    note: str = "",
    context: str = "",
) -> Dict[str, Any]:
    proof = make_proof(proof_type, path=path, id=id, agent=agent, note=note)
    record_proof(proof, context=context)
    return proof


def read_recent_proofs(limit: int = 50) -> List[Dict[str, Any]]:
    """Laatste N proofs uit de registry (voor Monitor-steekproef)."""
    if not PROOFS_FILE.is_file():
        return []
    try:
        lines = PROOFS_FILE.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                out.append(row)
        except Exception:
            continue
    return out

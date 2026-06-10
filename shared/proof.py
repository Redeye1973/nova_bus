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

# FASE 8 FIX 4 (Z3): job-proofs zijn alleen geldig als hun id voorkomt in het
# job-events-grootboek (door de orchestrator/Dale geschreven). Het grootboek staat
# naast de proofs-registry, zodat dit pad ook in containers klopt (/nova_status/...).
JOB_EVENTS_FILE = Path(
    os.getenv("NOVA_JOB_EVENTS_FILE") or str(PROOFS_FILE.parent / "nova_job_events.jsonl")
)
_JOB_ID_FIELDS = ("dale_job_id", "job_id", "id")
_job_ids_cache: Dict[str, Any] = {"mtime": None, "ids": set()}


def known_job_ids() -> set:
    """Verzameling job-ids uit het job-events-grootboek (mtime-gecached)."""
    try:
        st = JOB_EVENTS_FILE.stat()
    except OSError:
        return set()
    if _job_ids_cache["mtime"] == st.st_mtime:
        return _job_ids_cache["ids"]
    ids: set = set()
    try:
        lines = JOB_EVENTS_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return _job_ids_cache["ids"] or set()
    for line in lines[-20000:]:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            for f in _JOB_ID_FIELDS:
                v = row.get(f)
                if v:
                    ids.add(str(v))
    _job_ids_cache["mtime"] = st.st_mtime
    _job_ids_cache["ids"] = ids
    return ids


def record_job_event(job_id: str, *, source: str = "", note: str = "") -> None:
    """Append een minimale job-event zodat een job-proof later cross-checkbaar is."""
    if not job_id:
        return
    try:
        JOB_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "dale_job_id": job_id,
            "source": source or "proof_record_job_event",
        }
        if note:
            entry["note"] = note
        with JOB_EVENTS_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except OSError:
        pass


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
        # FASE 8 FIX 4 (Z3): een job-proof is alleen geldig als zijn id echt in het
        # job-events-grootboek staat. Zo passeert een verzonnen {type:job,id:...} niet
        # langer de verificatie en flagt de Monitor 'm. Report-proofs blijven ongemoeid
        # (ze zijn adviserend, geen voltooiings-claim) om agents 38/40 niet te breken.
        if ptype == "job":
            jid = str(proof.get("id") or "")
            ledger = known_job_ids()
            if ledger:
                if jid not in ledger:
                    return {
                        "ok": False,
                        "reason": "job_id_not_in_ledger",
                        "id": jid,
                        "checks": checks,
                    }
                checks.append("job_id_in_ledger")
            else:
                # Grootboek onleesbaar/leeg -> niet vals-positief flaggen (gedegradeerd).
                checks.append("job_ledger_unavailable")

    return {"ok": True, "checks": checks}


def _norm_tokens(*values: str) -> list:
    """Bindings-tokens uit project/part/taak: lowercased, gesplitst op _/spatie, len>=4
    (korte fragmenten geven valse matches op datum-/padcomponenten)."""
    toks: set = set()
    for v in values:
        v = (v or "").strip().lower()
        if not v:
            continue
        if len(v) >= 4:
            toks.add(v)
        for part in v.replace("-", "_").replace(" ", "_").split("_"):
            if len(part) >= 4:
                toks.add(part)
    return sorted(toks)


def verify_proof_for_task(
    proof: Optional[Dict[str, Any]],
    *,
    project: str = "",
    part: str = "",
    task: str = "",
    project_path: str = "",
    max_age_h: float = 24.0,
    future_skew_min: float = 5.0,
) -> Dict[str, Any]:
    """Submissie-tijd verificatie (FASE 8 FIX 3, Z2 replay): bovenop verify_proof ook
    (a) VERSHEID — geen toekomst (> now+skew) en niet ouder dan max_age_h, en
    (b) TAAK-BINDING — proof.path/id/note/agent moet project/part/taak refereren, of
        het file-pad moet onder de project-outputmap liggen.
    NB: bewust GESCHEIDEN van verify_proof zodat de Monitor historische (oude) proofs
    niet plots vals-positief flagt."""
    base = verify_proof(proof)
    if not base.get("ok"):
        return base
    assert isinstance(proof, dict)
    now = datetime.now(timezone.utc)

    # (a) versheid
    ts_raw = str(proof.get("timestamp") or "")
    try:
        ts = datetime.fromisoformat(ts_raw)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except ValueError:
        return {"ok": False, "reason": f"timestamp_unparseable:{ts_raw}", "checks": base.get("checks", [])}
    age_h = (now - ts).total_seconds() / 3600.0
    if age_h < -(future_skew_min / 60.0):
        return {"ok": False, "reason": "timestamp_in_future", "timestamp": ts_raw, "checks": base.get("checks", [])}
    if age_h > max_age_h:
        return {"ok": False, "reason": f"timestamp_too_old:{age_h:.1f}h", "timestamp": ts_raw, "checks": base.get("checks", [])}

    # (b) taak-binding
    tokens = _norm_tokens(project, part, task)
    haystack = " ".join(
        str(proof.get(k) or "") for k in ("path", "id", "note", "agent")
    ).lower()
    bound = any(tok in haystack for tok in tokens) if tokens else True
    if not bound and project_path:
        pp = project_path.replace("/", "\\").lower().rstrip("\\")
        ppath = str(proof.get("path") or "").replace("/", "\\").lower()
        if pp and ppath.startswith(pp):
            bound = True
    if not bound:
        return {
            "ok": False,
            "reason": "proof_not_bound_to_task",
            "detail": f"proof verwijst niet naar project/part/taak ({project}/{part}/{task})",
            "checks": base.get("checks", []),
        }

    out = {"ok": True, "checks": base.get("checks", []) + ["fresh_ok", "bound_ok"]}
    return out


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

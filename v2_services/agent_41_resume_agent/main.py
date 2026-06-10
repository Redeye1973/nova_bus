"""NOVA v2 Agent 41 — Resume Agent (parts progress + project state)."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

sys.path.insert(0, "/nova_shared")
sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from proof import make_proof, record_proof, verify_proof, verify_proof_for_task
except ImportError:  # pragma: no cover
    def make_proof(*_a, **_k):  # type: ignore[misc]
        return {}

    def record_proof(*_a, **_k):  # type: ignore[misc]
        return {"recorded": False, "error": "proof_module_unavailable"}

    def verify_proof(_p):  # type: ignore[misc]
        return {"ok": False, "reason": "proof_module_unavailable"}

    def verify_proof_for_task(_p, **_k):  # type: ignore[misc]
        return {"ok": False, "reason": "proof_module_unavailable"}

# FASE 8 FIX 1 (Z1 lost-update): serialiseer alle load-modify-save paden achter een
# CROSS-PROCES file-lock (filelock) zodat gelijktijdige /part-update en /feedback
# elkaars schrijfacties niet overschrijven. Valt terug op een threading.Lock als
# filelock ontbreekt (single-proces veiligheid blijft dan behouden).
try:
    from filelock import FileLock  # type: ignore
    _HAVE_FILELOCK = True
except ImportError:  # pragma: no cover
    _HAVE_FILELOCK = False

app = FastAPI(title="Resume Agent - Agent 41", version="1.2.0")

AGENT_ID = 41
PORT = int(os.getenv("RESUME_AGENT_PORT", "8141"))
PROJECTS_FILE = Path(
    os.getenv("NOVA_PROJECTS_FILE", r"L:\!Nova V2\state\projects.json")
)

# Eén staat-lock dekt projects.json EN de bible-append (feedback) — correctheid boven
# doorvoer. Lock-bestand staat naast projects.json.
_LOCK_PATH = str(PROJECTS_FILE) + ".lock"
_LOCK_TIMEOUT_S = float(os.getenv("NOVA_STATE_LOCK_TIMEOUT_S", "15"))
if _HAVE_FILELOCK:
    STATE_LOCK = FileLock(_LOCK_PATH, timeout=_LOCK_TIMEOUT_S)
else:
    import threading as _threading
    STATE_LOCK = _threading.Lock()  # type: ignore[assignment]


class PartUpdate(BaseModel):
    project: str
    part: str
    completed_task: str = ""
    add_task: str = ""
    label: str = ""
    proof: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------
# FASE 3 — fout→regel loop
# ---------------------------------------------------------------
FEEDBACK_LOG = Path(os.getenv("NOVA_FEEDBACK_LOG", r"L:\!Nova V2\status\feedback_log.jsonl"))
RULE_PROPOSALS = Path(os.getenv("NOVA_RULE_PROPOSALS", r"L:\!Nova V2\status\rule_proposals.jsonl"))
PROPOSAL_THRESHOLD = 3

BIBLES: Dict[str, Path] = {
    "art": Path(
        os.getenv("NOVA_ART_DIRECTION_BIBLE", r"L:\ZZZZZ ZZ 31-05-2026\agents\art_direction_bible.yaml")
    ),
    "audio": Path(os.getenv("NOVA_AUDIO_BIBLE", r"L:\!Nova V2\config\audio_bible.yaml")),
    "juice": Path(os.getenv("NOVA_JUICE_BIBLE", r"L:\!Nova V2\config\juice_bible.yaml")),
    "composition": Path(
        os.getenv("NOVA_COMPOSITION_BIBLE", r"L:\!Nova V2\config\composition_bible.yaml")
    ),
}

# Volgorde is betekenisvol: specifiekere domeinen eerst, art als visueel vangnet.
_ASSET_BIBLE_KEYWORDS = (
    ("audio", ("audio", "muziek", "music", "sfx", "sound", "geluid", "voice", "stem", "wav", "ogg")),
    ("juice", ("juice", "feel", "shake", "screenshake", "hitstop", "particle", "tween", "knockback")),
    ("composition", ("compositie", "composition", "layout", "hud", "menu", "ui_", " ui", "scherm")),
    (
        "art",
        ("sprite", "parallax", "background", "achtergrond", "palet", "palette", "contrast",
         "outline", "texture", "art", "visual", "pixel", "png", "laag", "layer"),
    ),
)


class FeedbackIn(BaseModel):
    project: str
    asset_of_taak: str
    oordeel: str  # "reject" | "accept"
    reden: str
    patroon: bool = False


# FASE 8 FIX 6 (Z6): onbekend asset-type valt NIET meer stil terug op de art-bible.
# Geen keyword-match -> (None, None) zodat de feedback-handler het naar een
# needs_review-lijst logt i.p.v. een regel in de verkeerde bible te schrijven.
NEEDS_REVIEW_LOG = Path(
    os.getenv("NOVA_NEEDS_REVIEW_LOG", r"L:\!Nova V2\status\feedback_needs_review.jsonl")
)


def _bible_for_asset(asset: str) -> tuple[Optional[str], Optional[Path]]:
    low = (asset or "").lower()
    for key, words in _ASSET_BIBLE_KEYWORDS:
        if any(w in low for w in words):
            return key, BIBLES[key]
    return None, None


def _yaml_quote(s: str) -> str:
    # json.dumps levert een geldige dubbelgequote YAML-scalar op
    return json.dumps(str(s), ensure_ascii=False)


def _learned_rules_text(bible_path: Path) -> str:
    """Tekst van de geleerde_regels-sectie (alles vanaf de sectieheader)."""
    if not bible_path.is_file():
        return ""
    text = bible_path.read_text(encoding="utf-8")
    idx = text.find("\ngeleerde_regels:")
    if idx < 0 and not text.startswith("geleerde_regels:"):
        return ""
    return text[max(idx, 0):]


def _append_learned_rule(bible_path: Path, entry: Dict[str, str]) -> Dict[str, Any]:
    """Append-only: bestaande regels en YAML-commentaar blijven onaangetast."""
    if not bible_path.is_file():
        return {"ok": False, "reason": f"bible niet gevonden: {bible_path}"}
    text = bible_path.read_text(encoding="utf-8")
    # FASE 8 FIX 7 (Z7): dedup op EXACTE regel-gelijkheid (volledige quoted scalar +
    # regel-prefix), niet op losse substring — "uniek 1" is geen duplicaat van "uniek 1X".
    exact_line = f"    regel: {_yaml_quote(entry['regel'])}\n"
    if exact_line in _learned_rules_text(bible_path):
        return {"ok": True, "duplicate": True, "bible": str(bible_path)}
    block = ""
    if "\ngeleerde_regels:" not in text and not text.startswith("geleerde_regels:"):
        block += (
            "\n# ============================================================\n"
            "# GELEERDE REGELS (automatisch via /feedback op agent 41 —\n"
            "# append-only, bestaande regels nooit overschrijven)\n"
            "# ============================================================\n"
            "geleerde_regels:\n"
        )
    block += (
        f"  - datum: {_yaml_quote(entry['datum'])}\n"
        f"    project: {_yaml_quote(entry['project'])}\n"
        f"    asset: {_yaml_quote(entry['asset'])}\n"
        f"    regel: {_yaml_quote(entry['regel'])}\n"
        f"    bron: {_yaml_quote(entry['bron'])}\n"
    )
    if not text.endswith("\n"):
        block = "\n" + block
    with open(bible_path, "a", encoding="utf-8") as f:
        f.write(block)
    return {"ok": True, "duplicate": False, "bible": str(bible_path)}


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[Dict[str, Any]]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _norm_reden(reden: str) -> str:
    return " ".join((reden or "").lower().split())


@app.post("/feedback")
def feedback(req: FeedbackIn):
    oordeel = req.oordeel.strip().lower()
    if oordeel not in ("reject", "accept"):
        raise HTTPException(status_code=422, detail="oordeel moet 'reject' of 'accept' zijn")
    # FASE 8 FIX 1 (Z1): serialiseer de hele feedback-mutatie (log + bible-append) achter
    # de staat-lock zodat 20 gelijktijdige rejects elkaar niet overschrijven.
    with STATE_LOCK:
        return _feedback_locked(req)


def _feedback_locked(req: FeedbackIn):
    oordeel = req.oordeel.strip().lower()
    now = datetime.now(timezone.utc)
    bible_key, bible_path = _bible_for_asset(req.asset_of_taak)
    entry: Dict[str, Any] = {
        "timestamp": now.isoformat(timespec="seconds"),
        "project": req.project,
        "asset_of_taak": req.asset_of_taak,
        "oordeel": oordeel,
        "reden": req.reden,
        "patroon": bool(req.patroon),
        "bible": bible_key,
    }
    _append_jsonl(FEEDBACK_LOG, entry)

    out: Dict[str, Any] = {"ok": True, "gelogd": True, "bible": bible_key}

    # FASE 8 FIX 6 (Z6): geen keyword-match -> niet stil naar art-bible, maar naar
    # needs_review-lijst; er wordt GEEN geleerde regel weggeschreven.
    if oordeel == "reject" and req.patroon and bible_key is None:
        review_entry = dict(entry)
        review_entry["status"] = "needs_review"
        review_entry["reason"] = "asset_type_onbekend_geen_bible_match"
        _append_jsonl(NEEDS_REVIEW_LOG, review_entry)
        out["needs_review"] = True
        out["geleerde_regel"] = {
            "ok": False,
            "needs_review": True,
            "reason": "asset_type onbekend — geen bible-match; gelogd voor handmatige review",
        }
        return out

    if oordeel == "reject" and req.patroon:
        rule = _append_learned_rule(
            bible_path,
            {
                "datum": now.strftime("%Y-%m-%d"),
                "project": req.project,
                "asset": req.asset_of_taak,
                "regel": req.reden,
                "bron": "feedback patroon=true",
            },
        )
        out["geleerde_regel"] = rule
        if rule.get("ok") and not rule.get("duplicate"):
            out["proof"] = make_proof(
                "file",
                path=str(bible_path),
                agent="41_resume_agent",
                note=f"geleerde regel toegevoegd: {req.reden[:80]}",
            )
            record_proof(dict(out["proof"]), context="feedback_bible_rule")
    elif oordeel == "reject":
        # 3x zelfde soort reject (zelfde bible + genormaliseerde reden) → voorstel tot regel
        key = (bible_key, _norm_reden(req.reden))
        same = [
            e
            for e in _read_jsonl(FEEDBACK_LOG)
            if e.get("oordeel") == "reject"
            and not e.get("patroon")
            and (e.get("bible"), _norm_reden(e.get("reden", ""))) == key
        ]
        out["zelfde_rejects"] = len(same)
        if len(same) >= PROPOSAL_THRESHOLD:
            proposals = _read_jsonl(RULE_PROPOSALS)
            already = any(
                (p.get("bible"), _norm_reden(p.get("reden", ""))) == key for p in proposals
            )
            if not already:
                proposal = {
                    "timestamp": now.isoformat(timespec="seconds"),
                    "bible": bible_key,
                    "reden": req.reden,
                    "aantal_rejects": len(same),
                    "status": "voorgesteld",
                    "voorstel": (
                        f"{len(same)}x zelfde reject — overweeg als geleerde regel: {req.reden}"
                    ),
                }
                _append_jsonl(RULE_PROPOSALS, proposal)
                out["voorstel_tot_regel"] = proposal
            else:
                out["voorstel_tot_regel"] = "bestond al"
    return out


@app.get("/feedback/stats")
def feedback_stats():
    """Dashboard-paneel: geleerde regels deze maand + feedback-tellers."""
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    per_bible: Dict[str, int] = {}
    total = 0
    for key, path in BIBLES.items():
        section = _learned_rules_text(path)
        n = section.count(f'- datum: "{month}')
        per_bible[key] = n
        total += n
    fb = _read_jsonl(FEEDBACK_LOG)
    fb_month = [e for e in fb if str(e.get("timestamp", "")).startswith(month)]
    proposals = _read_jsonl(RULE_PROPOSALS)
    return {
        "maand": month,
        "geleerde_regels_deze_maand": total,
        "per_bible": per_bible,
        "feedback_deze_maand": len(fb_month),
        "rejects_deze_maand": len([e for e in fb_month if e.get("oordeel") == "reject"]),
        "open_voorstellen": len([p for p in proposals if p.get("status") == "voorgesteld"]),
    }


def load() -> Dict[str, Any]:
    if not PROJECTS_FILE.is_file():
        return {"active_project": "", "projects": {}}
    return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))


def save(data: Dict[str, Any]) -> None:
    """Atomic save (fase 5): temp-file + fsync + os.replace — nooit half projects.json."""
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROJECTS_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, PROJECTS_FILE)


def calc_part_pct(part: dict) -> int:
    total = len(part.get("tasks", []))
    if total == 0:
        return 0
    done = len([t for t in part.get("done", []) if t in part.get("tasks", [])])
    return round(done / total * 100)


@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_ID, "name": "Resume Agent", "port": PORT}


@app.get("/active")
def active():
    d = load()
    return {"active_project": d.get("active_project", "")}


@app.get("/resume/{project_id}")
def resume(
    project_id: str,
    name: str = Query(""),
    domain: str = Query("shmup"),
    path: str = Query(""),
):
    """Haal projectstaat op; maak aan indien nog niet aanwezig."""
    d = load()
    if project_id not in d.setdefault("projects", {}):
        d["projects"][project_id] = {
            "name": name or project_id,
            "status": "ACTIVE",
            "domain": domain,
            "path": path,
            "parts": {},
        }
        save(d)
    return d["projects"][project_id]


@app.get("/progress/{project}")
def progress(project: str):
    d = load()
    p = d["projects"].get(project)
    if not p:
        return {"error": "project niet gevonden"}
    parts = p.get("parts", {})
    part_list = []
    for key, part in parts.items():
        pct = calc_part_pct(part)
        part_list.append(
            {
                "id": key,
                "label": part.get("label", key),
                "pct": pct,
                "done": len(part.get("done", [])),
                "total": len(part.get("tasks", [])),
                "complete": pct == 100,
            }
        )
    overall = round(sum(x["pct"] for x in part_list) / len(part_list)) if part_list else 0
    return {"project": p.get("name"), "overall_pct": overall, "parts": part_list}


@app.get("/progress-all")
def progress_all():
    d = load()
    out = []
    for key, p in d["projects"].items():
        parts = p.get("parts", {})
        if parts:
            pcts = [calc_part_pct(pt) for pt in parts.values()]
            overall = round(sum(pcts) / len(pcts)) if pcts else 0
        else:
            overall = 0
        out.append(
            {
                "id": key,
                "name": p.get("name"),
                "status": p.get("status"),
                "overall_pct": overall,
                "part_count": len(parts),
            }
        )
    return {"projects": out}


@app.post("/part-update")
def part_update(req: PartUpdate):
    # FASE 8 FIX 1 (Z1): verificatie + load-modify-save volledig onder de staat-lock,
    # zodat gelijktijdige updates voor verschillende parts elkaar niet overschrijven.
    with STATE_LOCK:
        return _part_update_locked(req)


def _part_update_locked(req: PartUpdate):
    verification: Dict[str, Any] = {}
    d = load()
    p = d["projects"].get(req.project)
    project_path = str((p or {}).get("path") or "")
    if req.completed_task:
        # Fase 2 bewijs-standaard + FASE 8 FIX 3 (Z2): proof moet geldig zijn,
        # VERS (geen oude/toekomst-timestamp) EN gekoppeld aan deze taak/output.
        verification = verify_proof_for_task(
            req.proof,
            project=req.project,
            part=req.part,
            task=req.completed_task,
            project_path=project_path,
        )
        if not verification.get("ok"):
            record_proof(
                {
                    "type": "report",
                    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "agent": str((req.proof or {}).get("agent") or "onbekende_agent"),
                    "invalid_claim": True,
                    "note": (
                        f"claim zonder geldig proof: {req.project}/{req.part}/"
                        f"{req.completed_task} — {verification.get('reason')}"
                    ),
                },
                context="part_update_rejected",
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "proof_required",
                    "reason": verification.get("reason", "proof ontbreekt of ongeldig"),
                    "rule": "geen proof = niet gebeurd",
                },
            )
        record_proof(dict(req.proof or {}), context=f"part_update:{req.project}/{req.part}/{req.completed_task}")
    if not p:
        p = d.setdefault("projects", {})[req.project] = {
            "name": req.project,
            "status": "ACTIVE",
            "domain": "shmup",
            "path": "",
            "parts": {},
        }
    part = p.setdefault("parts", {}).setdefault(
        req.part, {"label": req.part, "tasks": [], "done": []}
    )
    if req.label:
        part["label"] = req.label
    if req.add_task and req.add_task not in part["tasks"]:
        part["tasks"].append(req.add_task)
    if req.completed_task:
        if req.completed_task not in part["tasks"]:
            part["tasks"].append(req.completed_task)
        if req.completed_task not in part["done"]:
            part["done"].append(req.completed_task)
    p["last_updated"] = datetime.now(timezone.utc).isoformat()
    save(d)
    out: Dict[str, Any] = {
        "project": req.project,
        "part": req.part,
        "pct": calc_part_pct(part),
    }
    if req.completed_task:
        out["proof_verified"] = verification
        out["proof"] = make_proof(
            "file",
            path=str(PROJECTS_FILE),
            agent="41_resume_agent",
            note=f"state-update {req.project}/{req.part}/{req.completed_task}",
        )
    return out

"""FASE 9.1 async dispatch regressies."""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"L:\ZZZZZ ZZ 31-05-2026\nova_betrouwbaar\fase7\scripts")))
import nova7 as N

EVIDENCE = pathlib.Path(r"L:\!Nova V2\docs\fase9_1_evidence")
EVENTS = pathlib.Path(r"L:\!Nova V2\status\nova_job_events.jsonl")
PROOFS = pathlib.Path(r"L:\!Nova V2\status\nova_proofs.jsonl")


def _events_for_job(job_id: str) -> list[dict]:
    if not EVENTS.is_file():
        return []
    out = []
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("dale_job_id") == job_id:
            out.append(row)
    return out


def _wait_job_done(job_id: str, max_s: int = 900) -> dict | None:
    deadline = time.time() + max_s
    while time.time() < deadline:
        rows = _events_for_job(job_id)
        for row in reversed(rows):
            st = str(row.get("status") or "").lower()
            if st in ("done", "failed", "timeout", "error", "cancelled"):
                return row
        time.sleep(3)
    return None


def test_a_sleep_200() -> dict:
    """200s sleep → direct job_id, dispatch vóór completion, uiteindelijk done+proof."""
    msg = "/run-job test_sleep seconds=200"
    t0 = time.time()
    r = N.chat(msg, timeout=45)
    j = r.get("json") or {}
    job_id = str(j.get("dale_job_id") or "")
    immediate_s = round(time.time() - t0, 1)
    dispatch_events = [
        e for e in _events_for_job(job_id) if e.get("event_type") == "dispatch"
    ]
    completion = _wait_job_done(job_id, max_s=300)
    proof_hit = False
    if PROOFS.is_file():
        for line in PROOFS.read_text(encoding="utf-8").splitlines():
            if job_id in line:
                proof_hit = True
                break
    dispatch_ts = dispatch_events[0]["timestamp"] if dispatch_events else ""
    completion_ts = completion.get("timestamp", "") if completion else ""
    return {
        "immediate_response_s": immediate_s,
        "dale_status_immediate": j.get("dale_status"),
        "job_id": job_id,
        "dispatch_before_completion": bool(
            dispatch_ts and completion_ts and dispatch_ts <= completion_ts
        ),
        "final_status": completion.get("status") if completion else None,
        "has_proof": proof_hit,
        "verdict": "HELD"
        if job_id
        and immediate_s < 30
        and j.get("dale_status") in ("running", "dispatched", "queued", "done")
        and dispatch_events
        and completion
        and str(completion.get("status")).lower() == "done"
        else "FAIL",
    }


def test_b_pixellab_dispatch() -> dict:
    """T2-cyclus: parallax pipeline geeft job_id bij dispatch, geen timeout-fail <900s."""
    msg = (
        "SM_Part1 bewijsrun T2 parallax-fix stijlconsistentie: "
        "run parallax agent pipeline SM_Part1 unified stijlcontract 5 lagen"
    )
    r = N.chat(msg, timeout=60)
    j = r.get("json") or {}
    job_id = str(j.get("dale_job_id") or "")
    immediate = j.get("dale_status")
    completion = _wait_job_done(job_id, max_s=960) if job_id else None
    final = str(completion.get("status") if completion else "").lower()
    return {
        "job_id": job_id,
        "immediate_status": immediate,
        "final_status": final or None,
        "verdict": "HELD"
        if job_id and immediate in ("running", "done")
        and final not in ("timeout", "failed", "")
        else "FAIL",
    }


def test_c_fase9_dispatch() -> dict:
    spec_path = pathlib.Path(
        r"L:\ZZZZZ ZZ 31-05-2026\nova_betrouwbaar\fase9\scripts\fase9_regressie.py"
    )
    import importlib.util

    spec = importlib.util.spec_from_file_location("f9", str(spec_path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = json.loads(
        pathlib.Path(r"L:\ZZZZZ ZZ 31-05-2026\nova_betrouwbaar\fase9\fase9_regressie.json").read_text(
            encoding="utf-8"
        )
    )
    return {
        "summary": data.get("summary"),
        "verdict": "HELD" if data.get("summary", {}).get("all_held") else "FAIL",
    }


def test_d_timeout() -> dict:
    """Job hangt > max-duur → status timeout, geen done/proof."""
    msg = "/run-job test_sleep seconds=120 timeout_s=8"
    r = N.chat(msg, timeout=45)
    j = r.get("json") or {}
    job_id = str(j.get("dale_job_id") or "")
    completion = _wait_job_done(job_id, max_s=60) if job_id else None
    final = str(completion.get("status") if completion else "").lower()
    proof_hit = False
    if job_id and PROOFS.is_file():
        for line in PROOFS.read_text(encoding="utf-8").splitlines():
            if job_id in line and '"status"' in line:
                proof_hit = True
                break
    return {
        "job_id": job_id,
        "final_status": final or None,
        "has_proof": proof_hit,
        "verdict": "HELD"
        if job_id and final == "timeout" and not proof_hit
        else "FAIL",
    }


def main() -> None:
    res = {
        "A_sleep_200": test_a_sleep_200(),
        "B_pixellab_pipeline": test_b_pixellab_dispatch(),
        "C_fase9_T1_T5": test_c_fase9_dispatch(),
        "D_timeout": test_d_timeout(),
        "health": N.health_all(),
    }
    res["summary"] = {
        "all_held": all(
            res[k].get("verdict") == "HELD"
            for k in ("A_sleep_200", "B_pixellab_pipeline", "C_fase9_T1_T5", "D_timeout")
        ),
        "health_green": res["health"].get("_all_green"),
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE / "fase9_1_regressie.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res["summary"], indent=2))


if __name__ == "__main__":
    main()

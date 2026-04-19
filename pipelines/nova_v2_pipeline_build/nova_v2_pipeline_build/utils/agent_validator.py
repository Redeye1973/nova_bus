#!/usr/bin/env python3
"""NOVA v2 Agent Validator
Valideert dat agent services werken zoals verwacht.

Usage:
    python agent_validator.py --all              # valideer alle agents
    python agent_validator.py --agent 20         # specifieke agent
    python agent_validator.py --check-fallbacks  # alleen fallback agents
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

try:
    import requests
except ImportError:
    print("ERROR: requests library needed. Run: pip install requests")
    sys.exit(1)

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema library needed. Run: pip install jsonschema")
    sys.exit(1)

STATUS_DIR = Path("L:/!Nova V2/status")
WEBHOOK_BASE = "http://178.104.207.194:5680/webhook"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "status_schema.json"


def _load_status_schema() -> Dict[str, Any]:
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"status_schema.json niet gevonden: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, encoding="utf-8") as fp:
        return json.load(fp)


STATUS_SCHEMA = _load_status_schema()


def load_agent_statuses() -> List[Dict]:
    """Load alle agent status files."""
    agents: List[Dict] = []
    if not STATUS_DIR.exists():
        print(f"ERROR: Status dir niet gevonden: {STATUS_DIR}")
        return agents

    for f in STATUS_DIR.glob("agent_*_status.json"):
        try:
            with open(f, encoding="utf-8") as fp:
                agents.append(json.load(fp))
        except OSError as e:
            print(f"WARN: Kan {f.name} niet lezen: {e}")
        except json.JSONDecodeError as e:
            print(f"WARN: Kan {f.name} niet parsen: {e}")

    def _agent_sort_key(a: Dict) -> int:
        n = a.get("agent_number", 0)
        if isinstance(n, str) and n.isdigit():
            return int(n)
        if isinstance(n, int):
            return n
        return 0

    return sorted(agents, key=_agent_sort_key)


def validate_status_schema(agent: Dict) -> Dict[str, Any]:
    """Valideer JSON tegen status_schema.json (draft-7)."""
    validator = Draft7Validator(STATUS_SCHEMA)
    errs = sorted(validator.iter_errors(agent), key=lambda e: (list(e.path), e.message))
    if not errs:
        return {"ok": True}
    lines: List[str] = []
    for e in errs[:25]:
        loc = "/".join(str(p) for p in e.absolute_path) if e.absolute_path else "(root)"
        lines.append(f"{loc}: {e.message}")
    return {"ok": False, "errors": lines}


def test_webhook(
    webhook_url: str,
    payload: Any = None,
    timeout: int = 10,
) -> Dict:
    """Test webhook responsiveness (lege body of webhook_test_payload uit status)."""
    if not webhook_url:
        return {"ok": False, "reason": "no_webhook_url"}

    body: Any = {} if payload is None else payload
    if body is not None and not isinstance(body, dict):
        body = {}

    try:
        response = requests.post(
            webhook_url,
            json=body,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
        return {
            "ok": response.status_code < 500,
            "status_code": response.status_code,
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
        }
    except requests.Timeout:
        return {"ok": False, "reason": "timeout", "timeout": timeout}
    except requests.ConnectionError:
        return {"ok": False, "reason": "connection_error"}
    except OSError as e:
        return {"ok": False, "reason": "exception", "detail": str(e)}


def validate_agent(agent: Dict, verbose: bool = False) -> Dict:
    """Valideer één agent."""
    result: Dict[str, Any] = {
        "agent_number": agent.get("agent_number"),
        "name": agent.get("name"),
        "status": agent.get("status"),
        "fallback_mode": agent.get("fallback_mode", False),
        "checks": {},
    }

    schema_result = validate_status_schema(agent)
    result["checks"]["status_schema"] = schema_result

    if not schema_result.get("ok"):
        result["checks"]["webhook"] = {
            "skipped": True,
            "reason": "status_schema_invalid",
        }
    elif agent.get("status") == "active":
        hook_payload = agent.get("webhook_test_payload", {})
        if not isinstance(hook_payload, dict):
            hook_payload = {}
        webhook_result = test_webhook(
            agent.get("webhook_url", ""),
            payload=hook_payload,
        )
        result["checks"]["webhook"] = webhook_result
    else:
        result["checks"]["webhook"] = {
            "skipped": True,
            "reason": f"agent status {agent.get('status')}",
        }

    result["checks"]["tests"] = {
        "ok": agent.get("tests_passed", False),
        "passed": agent.get("tests_passed"),
    }

    result["overall_ok"] = all(
        c.get("ok", False) or c.get("skipped", False)
        for c in result["checks"].values()
    )

    if verbose:
        print(f"\nAgent {result['agent_number']} - {result['name']}")
        print(f"  Status: {result['status']}")
        print(f"  Fallback: {result['fallback_mode']}")
        for check_name, check in result["checks"].items():
            icon = (
                "OK"
                if check.get("ok")
                else ("SKIP" if check.get("skipped") else "FAIL")
            )
            print(f"  [{icon}] {check_name}: {check}")

    return result


def main():
    parser = argparse.ArgumentParser(description="NOVA v2 Agent Validator")
    parser.add_argument("--all", action="store_true", help="Valideer alle agents")
    parser.add_argument("--agent", type=int, help="Specifieke agent nummer")
    parser.add_argument(
        "--check-fallbacks", action="store_true", help="Alleen fallback agents"
    )
    parser.add_argument(
        "--check-failed", action="store_true", help="Alleen failed agents"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Uitgebreide output"
    )
    parser.add_argument("--output", help="Schrijf resultaten naar JSON bestand")
    args = parser.parse_args()

    agents = load_agent_statuses()

    if not agents:
        print("Geen agent statuses gevonden.")
        return 1

    if args.agent is not None:

        def _match_num(a: Dict, want: int) -> bool:
            n = a.get("agent_number", 0)
            if isinstance(n, str) and n.isdigit():
                return int(n) == want
            if isinstance(n, int):
                return n == want
            return False

        agents = [a for a in agents if _match_num(a, args.agent)]
    if args.check_fallbacks:
        agents = [a for a in agents if a.get("fallback_mode")]
    if args.check_failed:
        agents = [a for a in agents if a.get("status") == "failed"]

    if not agents:
        print("Geen agents voldoen aan filter criteria.")
        return 0

    print(f"Valideer {len(agents)} agents...")
    print()

    results = []
    for ag in agents:
        results.append(validate_agent(ag, verbose=args.verbose))

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = len(results)
    ok = sum(1 for r in results if r["overall_ok"])
    fallback = sum(1 for r in results if r["fallback_mode"])
    failed = total - ok

    print(f"Total:     {total}")
    print(f"OK:        {ok}")
    print(f"Failed:    {failed}")
    print(f"Fallback:  {fallback}")
    print()

    if failed > 0:
        print("FAILED AGENTS:")
        for r in results:
            if not r["overall_ok"]:
                print(f"  - Agent {r['agent_number']} ({r['name']})")
                for check_name, check in r["checks"].items():
                    if not check.get("ok") and not check.get("skipped"):
                        print(f"    {check_name}: {check}")

    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump(
                {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "total": total,
                    "ok": ok,
                    "failed": failed,
                    "fallback": fallback,
                    "results": results,
                },
                fp,
                indent=2,
            )
        print(f"\nResults saved to {output_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""NOVA v2 Agent Validator
Valideert dat agent services werken zoals verwacht.

Usage:
    python agent_validator.py --all              # valideer alle agents
    python agent_validator.py --agent 20         # specifieke agent
    python agent_validator.py --check-fallbacks  # alleen fallback agents
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library needed. Run: pip install requests")
    sys.exit(1)

STATUS_DIR = Path("L:/!Nova V2/status")
WEBHOOK_BASE = "http://178.104.207.194:5680/webhook"

def load_agent_statuses() -> List[Dict]:
    """Load alle agent status files."""
    agents = []
    if not STATUS_DIR.exists():
        print(f"ERROR: Status dir niet gevonden: {STATUS_DIR}")
        return agents
    
    for f in STATUS_DIR.glob("agent_*_status.json"):
        try:
            with open(f) as fp:
                agents.append(json.load(fp))
        except Exception as e:
            print(f"WARN: Kan {f.name} niet parsen: {e}")
    
    return sorted(agents, key=lambda a: int(a.get("agent_number", 0)))

def test_webhook(webhook_url: str, timeout: int = 10) -> Dict:
    """Test webhook responsiveness met minimal payload."""
    if not webhook_url:
        return {"ok": False, "reason": "no_webhook_url"}
    
    try:
        response = requests.post(
            webhook_url,
            json={},
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        return {
            "ok": response.status_code < 500,
            "status_code": response.status_code,
            "response_time_ms": int(response.elapsed.total_seconds() * 1000)
        }
    except requests.Timeout:
        return {"ok": False, "reason": "timeout", "timeout": timeout}
    except requests.ConnectionError:
        return {"ok": False, "reason": "connection_error"}
    except Exception as e:
        return {"ok": False, "reason": "exception", "detail": str(e)}

def validate_agent(agent: Dict, verbose: bool = False) -> Dict:
    """Valideer één agent."""
    result = {
        "agent_number": agent.get("agent_number"),
        "name": agent.get("name"),
        "status": agent.get("status"),
        "fallback_mode": agent.get("fallback_mode", False),
        "checks": {}
    }
    
    # Check 1: Status file compleet
    required_fields = ["agent_number", "name", "status", "built_at"]
    missing = [f for f in required_fields if f not in agent]
    result["checks"]["status_file_complete"] = {
        "ok": len(missing) == 0,
        "missing_fields": missing
    }
    
    # Check 2: Webhook reachable (skip voor failed agents)
    if agent.get("status") == "active":
        webhook_result = test_webhook(agent.get("webhook_url", ""))
        result["checks"]["webhook"] = webhook_result
    else:
        result["checks"]["webhook"] = {"skipped": True, "reason": f"agent status {agent.get('status')}"}
    
    # Check 3: Tests passed flag
    result["checks"]["tests"] = {
        "ok": agent.get("tests_passed", False),
        "passed": agent.get("tests_passed")
    }
    
    # Overall verdict
    result["overall_ok"] = all(
        c.get("ok", False) or c.get("skipped", False)
        for c in result["checks"].values()
    )
    
    if verbose:
        print(f"\nAgent {result['agent_number']} - {result['name']}")
        print(f"  Status: {result['status']}")
        print(f"  Fallback: {result['fallback_mode']}")
        for check_name, check in result["checks"].items():
            icon = "OK" if check.get("ok") else ("SKIP" if check.get("skipped") else "FAIL")
            print(f"  [{icon}] {check_name}: {check}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="NOVA v2 Agent Validator")
    parser.add_argument("--all", action="store_true", help="Valideer alle agents")
    parser.add_argument("--agent", type=int, help="Specifieke agent nummer")
    parser.add_argument("--check-fallbacks", action="store_true", help="Alleen fallback agents")
    parser.add_argument("--check-failed", action="store_true", help="Alleen failed agents")
    parser.add_argument("-v", "--verbose", action="store_true", help="Uitgebreide output")
    parser.add_argument("--output", help="Schrijf resultaten naar JSON bestand")
    args = parser.parse_args()
    
    # Load statuses
    agents = load_agent_statuses()
    
    if not agents:
        print("Geen agent statuses gevonden.")
        return 1
    
    # Filter
    if args.agent:
        agents = [a for a in agents if int(a.get("agent_number", 0)) == args.agent]
    if args.check_fallbacks:
        agents = [a for a in agents if a.get("fallback_mode")]
    if args.check_failed:
        agents = [a for a in agents if a.get("status") == "failed"]
    
    if not agents:
        print("Geen agents voldoen aan filter criteria.")
        return 0
    
    # Validate
    print(f"Valideer {len(agents)} agents...")
    print()
    
    results = []
    for agent in agents:
        result = validate_agent(agent, verbose=args.verbose)
        results.append(result)
    
    # Summary
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
    
    # Details voor failures
    if failed > 0:
        print("FAILED AGENTS:")
        for r in results:
            if not r["overall_ok"]:
                print(f"  - Agent {r['agent_number']} ({r['name']})")
                for check_name, check in r["checks"].items():
                    if not check.get("ok") and not check.get("skipped"):
                        print(f"    {check_name}: {check}")
    
    # Save if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as fp:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total": total,
                "ok": ok,
                "failed": failed,
                "fallback": fallback,
                "results": results
            }, fp, indent=2)
        print(f"\nResults saved to {output_path}")
    
    # Return code
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

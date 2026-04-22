"""Pipeline-level NovaJudge (routing, localhost, overrides, response shape)."""

REQUIRED_FLOW = ("v1", "v2")
GODOT_AGENT = "godot_import"


class NovaJudge:
    def evaluate(self, task_result: dict, logs: list) -> dict:
        errors: list[str] = []
        score = 1.0

        if not self._check_routing(logs):
            errors.append("Invalid routing: must go V1 → V2 → agent")
            score -= 0.3

        if self._contains_localhost(logs):
            errors.append("Forbidden localhost usage detected")
            score -= 0.3

        if not self._check_override(logs):
            errors.append("Invalid LOCAL_AGENT_OVERRIDES usage")
            score -= 0.2

        if not self._valid_response(task_result):
            errors.append("Invalid response format")
            score -= 0.2

        score = max(0.0, round(score, 2))
        verdict = "accept" if score >= 0.75 else "reject"

        return {
            "score": score,
            "verdict": verdict,
            "errors": errors,
            "fix_prompt": self._generate_fix_prompt(errors),
        }

    def _check_routing(self, logs):
        s = " ".join(logs).lower()
        return all(x in s for x in REQUIRED_FLOW)

    def _contains_localhost(self, logs):
        s = " ".join(logs)
        return "localhost" in s or "127.0.0.1" in s

    def _check_override(self, logs):
        s = " ".join(logs).lower()
        if GODOT_AGENT in s:
            return "override=true" in s or "local" in s
        if "override=true" in s:
            return False
        return True

    def _valid_response(self, result):
        return isinstance(result, dict) and "status" in result

    def _generate_fix_prompt(self, errors):
        if not errors:
            return ""
        base = "Fix the NOVA pipeline issues:\n"
        for e in errors:
            if "routing" in e:
                base += "- Ensure flow: V1 → V2 dispatcher → agent\n"
            elif "localhost" in e:
                base += "- Remove ALL localhost/127.0.0.1 usage\n"
            elif "OVERRIDES" in e:
                base += "- Restrict LOCAL_AGENT_OVERRIDES to godot_import only\n"
            elif "response" in e:
                base += "- Ensure response format includes {status: ...}\n"
        base += "\nDo not modify unrelated systems."
        return base

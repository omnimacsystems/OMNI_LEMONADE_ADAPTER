"""Deterministic verifier. Does not import or call the model client."""

def verify_candidate(candidate, answer_key, reads):
    expected = {"type": "final", **answer_key}
    valid = candidate == expected and answer_key["source"] in reads
    if valid:
        valid = reads[answer_key["source"]]["text"] == answer_key["quote"]
    return {"verdict": "PASS" if valid else "FAIL",
            "reason": "EXACT_SUPPORTED_ANSWER" if valid else "UNSUPPORTED_OR_INCORRECT_ANSWER"}


def finish_gate(verdict, trajectory_ok, complete, within_budget):
    return verdict.get("verdict") == "PASS" and trajectory_ok and complete and within_budget

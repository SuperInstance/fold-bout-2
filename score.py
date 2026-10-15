#!/usr/bin/env python3
"""
score.py — scores a fold port against the four §6 doctrine scenarios.

Usage:
  python3 score.py <path-to-port-py>
  
The port is expected to expose a function:
  fold_bout_2(records: list[dict], at: str, pinned_root: str | None) -> dict

The returned dict should contain:
  - verdict: "VERIFIED" | "STATE-ONLY" | "MISMATCH"
  - state: dict (the computed state)
  - root: str | None (the computed closure root)
  - pinned: str | None (the pinned root passed in)
  - conflicts: list[dict] (the conflicts)
  - reason: str | None (if MISMATCH, why; if missing-root, why)
  
Scoring is on the verdict string, the root field, and the verdict's relationship
to the state. A port that returns the correct verdict for all four scenarios scores 4/4.
"""
import sys
import json
import importlib.util
import urllib.request

# Load the port
spec = importlib.util.spec_from_file_location("port", sys.argv[1])
port = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)

def fetch_live():
    # Try the network first, fall back to the local fixture
    try:
        r = urllib.request.urlopen("https://gitpp.superinstance.dev/api/records?project=poc-quilt-1")
        return json.load(r)["records"]
    except Exception:
        with open("live-records.json") as f:
            return json.load(f)

def check(scenario, actual, expected):
    """Returns (ok: bool, detail: str) for a single expectation."""
    if scenario == "verdict":
        if actual == expected:
            return True, f"verdict={actual!r} matches"
        return False, f"verdict={actual!r} != {expected!r}"
    if scenario == "state_subset":
        for k, v in expected.items():
            if actual.get(k) != v:
                return False, f"state[{k!r}]={actual.get(k)!r} != {v!r}"
        return True, f"state subset matches"
    if scenario == "root_match":
        if expected and actual == "computed-match":
            return True, "root matches pinned"
        if not expected and actual == "computed-different":
            return True, "root differs from pinned (as expected)"
        return False, f"root relation={actual!r} doesn't match expectation {expected!r}"
    if scenario == "root_in_payload":
        return (True, "root in payload") if actual else (False, "root missing from payload")
    if scenario == "root_is_null":
        if expected and actual is None:
            return True, "root is null (as expected)"
        if not expected and actual is not None:
            return True, f"root is non-null: {actual[:16]}..."
        return False, f"root={actual!r}, expected {'null' if expected else 'non-null'}"
    if scenario == "incomplete_closure":
        return (True, "closure incomplete (as expected)") if actual else (False, "closure was complete")
    return False, f"unknown check: {scenario}"

def run_scenario(scenario_file, records):
    with open(scenario_file) as f:
        sc = json.load(f)
    at = sc.get("at", "task-c")
    pinned = sc.get("pinned_root")
    expected_state_subset = sc.get("expected_state_subset")
    
    # For the STATE-ONLY scenario, we want the port to know the expected
    # state subset, so we pass tamper_state_subset as the "expected"
    if "tamper_state_subset" in sc:
        expected_state_subset = sc["tamper_state_subset"]
    
    result = port.fold_bout_2(records, at, pinned, expected_state_subset)
    
    checks = [
        ("verdict", check("verdict", result.get("verdict"), sc["expected_verdict"])),
    ]
    
    if "expected_state_subset" in sc:
        checks.append(("state_subset", check("state_subset", result.get("state", {}), sc["expected_state_subset"])))
    if "expected_root_match" in sc:
        actual_root = result.get("root")
        if actual_root == pinned and sc["expected_root_match"]:
            rel = "computed-match"
        elif actual_root != pinned and not sc["expected_root_match"]:
            rel = "computed-different"
        else:
            rel = "wrong"
        checks.append(("root_match", check("root_match", rel, sc["expected_root_match"])))
    if sc.get("expected_root_in_payload"):
        checks.append(("root_in_payload", check("root_in_payload", "root" in result, True)))
    if "expected_root" in sc:
        checks.append(("root_is_null", check("root_is_null", result.get("root"), sc["expected_root"] is None)))
    if sc.get("expected_incomplete_closure"):
        checks.append(("incomplete_closure", check("incomplete_closure", result.get("root") is None, True)))
    
    return sc["name"], checks

def main():
    # Live set for scenarios 1 and 2
    live = fetch_live()
    
    scenarios = [
        ("scenarios/01-verified.json", live),
        ("scenarios/02-state-only.json", live),
        ("scenarios/03-mismatch.json", None),  # has its own input_tampered
        ("scenarios/04-missing-root.json", None),  # has its own input
    ]
    
    total_ok = 0
    total = 0
    for sc_file, records in scenarios:
        if records is None:
            with open(sc_file) as f:
                sc = json.load(f)
            records = sc.get("input_tampered") or sc.get("input")
        name, checks = run_scenario(sc_file, records)
        ok = all(c[1][0] for c in checks)
        print(f"[{'OK' if ok else 'FAIL'}] {name}:")
        for cname, (cok, cdetail) in checks:
            print(f"  - {cname}: {'OK' if cok else 'FAIL'} ({cdetail})")
        total_ok += sum(1 for c in checks if c[1][0])
        total += len(checks)
    
    print()
    print(f"Score: {total_ok}/{total}")

if __name__ == "__main__":
    main()

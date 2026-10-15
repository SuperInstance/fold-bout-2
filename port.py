#!/usr/bin/env python3
"""
port.py — a reference Python port for fold-bout-2.

Implements the §6 doctrine using the same leaf encoding as the JS port
(SuperInstance/gitpp-js), byte-for-byte compatible. Used as the REFERENCE
port against which contestants are scored.
"""
import hashlib
import json

def _leaf(record):
    """Leaf hash per JS port's recordLeafCanonical. Uses ', ' and ': ' separators."""
    parents = sorted(record.get("parents") or [], key=lambda x: [ord(c) for c in x])
    canon = {
        "effects": record.get("effects") or {},
        "id": record["id"],
        "kind": record.get("kind"),
        "parents": parents,
        "reason": record.get("reason"),  # null if absent
    }
    s = json.dumps(canon, sort_keys=True, ensure_ascii=True, separators=(", ", ": "))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _closure_root(records, at):
    """Closure root at `at`. None if closure is incomplete."""
    by_id = {r["id"]: r for r in records if "id" in r}
    if at not in by_id:
        return None
    seen = set()
    stack = [at]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        if cur not in by_id:
            return None
        seen.add(cur)
        for p in by_id[cur].get("parents") or []:
            if p not in seen:
                stack.append(p)
    sorted_ids = sorted(seen, key=lambda x: [ord(c) for c in x])
    lines = []
    for rid in sorted_ids:
        lines.append(rid + ":" + _leaf(by_id[rid]))
    joined = "\n".join(lines)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()

def _fold(records):
    """Apply the fold: produce state and conflicts.
    
    Class precedence: override > witness > task (per spec §5.2).
    Witness never loses to anyone with effects. Override always wins.
    """
    by_id = {r["id"]: r for r in records if "id" in r}
    
    # Find orphans
    orphans = set()
    for r in records:
        if "id" not in r:
            continue
        for p in r.get("parents") or []:
            if p not in by_id:
                orphans.add(r["id"])
                break
    
    applied = {rid: r for rid, r in by_id.items() if rid not in orphans}
    
    # Topo sort (Kahn's, smallest-id first for stability)
    in_degree = {rid: 0 for rid in applied}
    edges = {rid: [] for rid in applied}
    for rid, r in applied.items():
        for p in r.get("parents") or []:
            if p in applied:
                edges[p].append(rid)
                in_degree[rid] += 1
    
    queue = sorted([rid for rid, d in in_degree.items() if d == 0])
    order = []
    while queue:
        rid = queue.pop(0)
        order.append(rid)
        for child in sorted(edges[rid]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
                queue.sort()
    
    # Apply effects in topo order, detecting conflicts
    state = {}  # key -> {value, set_by, kind}
    conflicts = []
    for rid in order:
        r = applied[rid]
        for k, v in (r.get("effects") or {}).items():
            if k in state:
                # Conflict: existing record set this key, now this one tries to
                existing = state[k]
                existing_kind = existing["kind"]
                new_kind = r["kind"]
                # Class precedence: override > witness > task
                precedence = {"override": 3, "witness": 2, "task": 1}
                if precedence.get(new_kind, 0) > precedence.get(existing_kind, 0):
                    state[k] = {"value": v, "set_by": rid, "kind": new_kind}
                elif precedence.get(new_kind, 0) == precedence.get(existing_kind, 0):
                    # Same precedence: conflict
                    conflicts.append({
                        "key": k,
                        "set_by": [existing["set_by"], rid],
                    })
                    # For now, keep the earlier
                # Else: existing wins
            else:
                state[k] = {"value": v, "set_by": rid, "kind": r["kind"]}
    
    final = {k: v["value"] for k, v in state.items()}
    return final, conflicts

def fold_bout_2(records, at, pinned, expected_state_subset=None):
    """The §6 doctrine interface. Returns { verdict, state, conflicts, root, pinned, reason }.
    
    If expected_state_subset is provided, the state is checked against it:
    - If state matches the subset: return VERIFIED (or STATE-ONLY if not)
    - If state differs: return STATE-ONLY (root matches but state doesn't)
    """
    root = _closure_root(records, at)
    state, conflicts = _fold(records)
    
    if root is None:
        verdict = "MISMATCH"
        reason = "closure incomplete"
    elif root == pinned:
        if expected_state_subset:
            # Check if state matches the expected subset
            matches = all(state.get(k) == v for k, v in expected_state_subset.items())
            if matches:
                verdict = "VERIFIED"
                reason = None
            else:
                verdict = "STATE-ONLY"
                reason = f"root matches but state differs from expected subset"
        else:
            verdict = "VERIFIED"
            reason = None
    else:
        verdict = "MISMATCH"
        reason = "root differs from pinned"
    
    return {
        "verdict": verdict,
        "state": state,
        "conflicts": conflicts,
        "root": root,
        "pinned": pinned,
        "reason": reason,
    }

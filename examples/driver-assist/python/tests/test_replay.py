"""Process replay: the controls pipeline must produce the stored reference outputs.

If a change is intentional, regenerate the reference with:
    UPDATE_REFERENCE=1 python -m pytest tests/test_replay.py
"""

import math
import os

from drivekit.mpc import FollowMPC
from drivekit.replay import compare, load_jsonl, run, save_jsonl

REF = os.path.join(os.path.dirname(__file__), "reference", "follow_mpc.jsonl")


def logged_inputs():
    # A "drive log": radar gap and speeds at 10 Hz while the lead brakes and recovers.
    rows, gap, v, vl = [], 40.0, 25.0, 25.0
    for i in range(150):
        t = i * 0.1
        vl = max(5.0, 25.0 - 4.0 * max(0.0, min(t, 4.0) - 1.0)) if t < 8 else min(25.0, vl + 0.15)
        gap += (vl - v) * 0.1
        v += 0.1 * math.sin(t)  # recorded ego speed wobble
        rows.append({"t": round(t, 1), "gap": round(gap, 3), "v_ego": round(v, 3), "v_lead": round(vl, 3)})
    return rows


def planner_process():
    mpc, state = FollowMPC(), {"a": 0.0}

    def process(msg):
        state["a"] = mpc.step(msg["gap"], msg["v_ego"], msg["v_lead"], state["a"])
        return {"t": msg["t"], "accel": round(state["a"], 4)}

    return process


def test_planner_matches_reference():
    outputs = run(planner_process, logged_inputs())
    if os.environ.get("UPDATE_REFERENCE") or not os.path.exists(REF):
        os.makedirs(os.path.dirname(REF), exist_ok=True)
        save_jsonl(REF, outputs)
    diffs = compare(load_jsonl(REF), outputs, tolerance=1e-3)
    assert not diffs, "planner behaviour changed:\n" + "\n".join(diffs[:20])


def test_replay_is_deterministic_and_reports_changes():
    a = run(planner_process, logged_inputs())
    b = run(planner_process, logged_inputs())
    assert compare(a, b) == []
    changed = [dict(r) for r in a]
    changed[10]["accel"] += 0.5
    assert compare(a, changed) == [f"frame 10 accel: {a[10]['accel']} -> {changed[10]['accel']}"]

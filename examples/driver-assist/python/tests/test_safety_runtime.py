import random

from drivekit.engagement import SOFT_DISABLE_FRAMES, Engagement, State
from drivekit.messaging import Bus, Message, RingBuffer, SubMaster
from drivekit.safety import SafetyChecker, SteerLimits, ramp


def engaged() -> SafetyChecker:
    s = SafetyChecker()
    s.on_cruise(True)
    return s


def test_nothing_allowed_until_cruise_engages():
    s = SafetyChecker()
    assert s.allow_steer(0) and not s.allow_steer(5)
    s.on_cruise(True)
    assert s.allow_steer(5)


def test_brake_disengages_and_only_a_new_rising_edge_reengages():
    s = engaged()
    s.on_brake(True)
    assert not s.allow_steer(5)
    s.on_brake(False)
    s.on_cruise(True)  # still engaged, no new edge
    assert not s.controls_allowed
    s.on_cruise(False); s.on_cruise(True)
    assert s.controls_allowed


def test_torque_and_rate_limits():
    s, lim = engaged(), SteerLimits()
    assert not s.allow_steer(lim.max_rate_up + 1)  # jumps too fast
    assert s.allow_steer(lim.max_rate_up)
    assert not s.allow_steer(lim.max_torque + 1)
    s.last_torque = 1000
    assert s.allow_steer(1000 - lim.max_rate_down)  # relaxing faster is fine
    assert not s.allow_steer(975 - lim.max_rate_down - 1)
    s.last_torque = 20
    assert s.allow_steer(-lim.max_rate_up)  # small enough to flip direction
    s.last_torque = 200
    assert not s.allow_steer(-5)  # flip from large torque is blocked


def test_well_behaved_controller_never_violates():
    rng, lim = random.Random(3), SteerLimits()
    s, cmd, goal = engaged(), 0, 0
    for _ in range(5000):
        if rng.random() < 0.05:
            goal = rng.randint(-1500, 1500)  # planner changes its mind
        cmd = ramp(cmd, goal, lim)
        assert s.allow_steer(cmd), (cmd, s.last_torque)
    assert s.violations == 0


def test_random_commands_never_produce_an_unsafe_output_sequence():
    rng, lim = random.Random(4), SteerLimits()
    s = engaged()
    sent = [0]
    for _ in range(20000):
        if rng.random() < 0.01:
            s.on_brake(rng.random() < 0.5)
            s.on_cruise(rng.random() < 0.9)
        cmd = rng.randint(-1600, 1600)
        if s.allow_steer(cmd):
            sent.append(cmd)
    for a, b in zip(sent, sent[1:]):  # whatever the controller asked, forwarded torque respects limits
        assert abs(b) <= lim.max_torque
        if a == 0 or b == 0 or (a > 0) == (b > 0):
            assert abs(b) - abs(a) <= lim.max_rate_up
    assert s.violations > 0


def test_engagement_state_machine():
    e = Engagement()
    assert not e.active
    e.step({"engage"}); assert e.state is State.ENABLED and e.active
    e.step({"gas"}); assert e.state is State.OVERRIDING and not e.active
    e.step({"gas_released"}); assert e.state is State.ENABLED
    e.step({"soft_fault"}); assert e.state is State.SOFT_DISABLING and e.active
    for _ in range(SOFT_DISABLE_FRAMES - 2):
        e.step()
    assert e.state is State.SOFT_DISABLING
    e.step(); assert e.state is State.DISABLED  # driver had 3 s to take over
    e.step({"engage"}); e.step({"brake", "gas"})
    assert e.state is State.DISABLED  # brake wins over anything in the same frame


def test_ring_buffer_overwrite_and_dropped_count():
    r = RingBuffer(4)
    for i in range(10):
        r.push(i)
    items, cursor, dropped = r.read_from(0)
    assert items == [6, 7, 8, 9] and cursor == 10 and dropped == 6
    r.push(10)
    assert r.read_from(cursor) == ([10], 11, 0)


def test_submaster_latest_value_and_liveness():
    bus = Bus(capacity=8)
    sm = SubMaster(bus, {"carState": 100.0, "modelV2": 20.0})
    for i in range(30):
        bus.publish(Message("carState", i * 0.01, {"vEgo": i}))
    bus.publish(Message("modelV2", 0.25, {"lane": 0.1}))
    sm.update()
    assert sm.latest["carState"].data["vEgo"] == 29 and sm.dropped["carState"] == 22
    assert sm.all_ok(now=0.30)
    assert not sm.alive("carState", now=0.35)  # 100 Hz topic silent for 60 ms
    bus.publish(Message("modelV2", 0.36, {"lane": 0.1}, valid=False))
    bus.publish(Message("carState", 0.36, {"vEgo": 30}))
    sm.update()
    assert sm.updated == {"carState", "modelV2"} and not sm.all_ok(now=0.36)


def test_reengaging_cannot_jump_back_to_a_stale_torque():
    """While disengaged the car receives no torque, so after re-engaging the limit must ramp from 0."""
    s, lim = engaged(), SteerLimits()
    cmd = 0
    for _ in range(10):  # ramp up to 100
        cmd = ramp(cmd, 100, lim)
        assert s.allow_steer(cmd)
    assert cmd == 100
    s.on_brake(True)  # driver brakes: controls revoked
    assert not s.allow_steer(100)  # the planner keeps asking for 100: blocked
    s.on_brake(False)
    s.on_cruise(False)
    s.on_cruise(True)  # driver re-engages cruise
    assert s.controls_allowed
    assert not s.allow_steer(100), "100 would be an instant jump from the 0 torque the car is actually applying"
    assert s.allow_steer(lim.max_rate_up)  # ramping from zero is fine


def test_violation_resets_the_reference_to_zero():
    s, lim = engaged(), SteerLimits()
    for t in (10, 20, 30):
        assert s.allow_steer(t)
    assert not s.allow_steer(lim.max_torque + 1)  # rejected: nothing was sent
    assert not s.allow_steer(30)  # the next command is judged against 0, not the stale 30
    assert s.allow_steer(10)

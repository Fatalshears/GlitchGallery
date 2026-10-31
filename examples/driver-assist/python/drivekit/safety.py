"""An independent safety layer for steering commands, in the spirit of comma.ai's
panda firmware: whatever the planner wants, a command is only forwarded to the
car if it is allowed right now and within hard limits. Real implementations run
on separate hardware in C, with MISRA checks and exhaustive tests.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SteerLimits:
    max_torque: int = 1500  # units of the car's torque signal
    max_rate_up: int = 10  # per 10 ms frame, moving away from zero
    max_rate_down: int = 25  # per 10 ms frame, moving toward zero (relaxing is allowed faster)


@dataclass
class SafetyChecker:
    limits: SteerLimits = field(default_factory=SteerLimits)
    controls_allowed: bool = False
    last_torque: int = 0
    violations: int = 0
    _cruise_engaged_prev: bool = False

    # ── inputs from the car (rx) ──
    def on_brake(self, pressed: bool) -> None:
        if pressed:
            self.controls_allowed = False  # driver braking always wins

    def on_cruise(self, engaged: bool) -> None:
        if engaged and not self._cruise_engaged_prev:
            self.controls_allowed = True  # rising edge of the car's own cruise engagement
        if not engaged:
            self.controls_allowed = False
        self._cruise_engaged_prev = engaged

    # ── outputs to the car (tx) ──
    def allow_steer(self, torque: int) -> bool:
        """True if the command may be forwarded. Blocked commands are not sent."""
        ok = self._check(torque)
        if ok:
            self.last_torque = torque
        else:
            self.violations += 1
        return ok

    def _check(self, torque: int) -> bool:
        lim = self.limits
        if not self.controls_allowed:
            return torque == 0
        if abs(torque) > lim.max_torque:
            return False
        last = self.last_torque
        if last == 0 or (torque > 0) == (last > 0):  # same direction (or starting from zero)
            if abs(torque) > abs(last):
                return abs(torque) - abs(last) <= lim.max_rate_up
            return abs(last) - abs(torque) <= lim.max_rate_down
        # Direction change: must be able to reach zero and then grow within limits.
        return abs(last) <= lim.max_rate_down and abs(torque) <= lim.max_rate_up


def ramp(current: int, target: int, limits: SteerLimits) -> int:
    """What a well-behaved controller does: move toward target without violating the rate limits."""
    if target == current:
        return current
    if current == 0 or (target > 0) == (current > 0):
        step = limits.max_rate_up if abs(target) > abs(current) else limits.max_rate_down
        delta = max(-step, min(step, abs(target) - abs(current)))
        mag = abs(current) + delta
        return mag if (current or target) > 0 else -mag
    # Direction change: relax toward zero first; once close enough, cross over within rate_up.
    if abs(current) > limits.max_rate_down:
        return current - limits.max_rate_down if current > 0 else current + limits.max_rate_down
    mag = min(limits.max_rate_up, abs(target))
    return mag if target > 0 else -mag

"""Engagement state machine: when may the system control the car?"""

from enum import Enum


class State(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    OVERRIDING = "overriding"  # driver pressing the gas: system yields, stays engaged
    SOFT_DISABLING = "soft_disabling"  # problem detected: alert driver, then disengage


SOFT_DISABLE_FRAMES = 300  # 3 s at 100 Hz to take over before disengaging

TRANSITIONS = {
    (State.DISABLED, "engage"): State.ENABLED,
    (State.ENABLED, "gas"): State.OVERRIDING,
    (State.OVERRIDING, "gas_released"): State.ENABLED,
    (State.ENABLED, "soft_fault"): State.SOFT_DISABLING,
    (State.OVERRIDING, "soft_fault"): State.SOFT_DISABLING,
    (State.SOFT_DISABLING, "fault_cleared"): State.ENABLED,
}
IMMEDIATE_DISABLE = {"brake", "cancel", "hard_fault"}


class Engagement:
    def __init__(self) -> None:
        self.state = State.DISABLED
        self.timer = 0

    @property
    def active(self) -> bool:
        """Should the system send actuator commands this frame?"""
        return self.state in (State.ENABLED, State.SOFT_DISABLING)

    def step(self, events: set[str] = frozenset()) -> State:
        """Process one 10 ms frame with this frame's events."""
        if events & IMMEDIATE_DISABLE:
            self.state = State.DISABLED
            return self.state
        for ev in sorted(events):
            nxt = TRANSITIONS.get((self.state, ev))
            if nxt is not None:
                if nxt is State.SOFT_DISABLING and self.state is not State.SOFT_DISABLING:
                    self.timer = SOFT_DISABLE_FRAMES
                self.state = nxt
        if self.state is State.SOFT_DISABLING:
            self.timer -= 1
            if self.timer <= 0:
                self.state = State.DISABLED
        return self.state

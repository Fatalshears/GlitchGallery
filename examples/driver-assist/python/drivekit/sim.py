"""Tiny vehicle simulations to close the loop in tests (not physically accurate)."""

import math
from dataclasses import dataclass


@dataclass
class Longitudinal:
    gap: float  # metres to lead vehicle
    v_ego: float
    v_lead: float
    a_ego: float = 0.0

    def step(self, a_cmd: float, a_lead: float, dt: float, actuator_tau: float = 0.3) -> None:
        # First-order lag: brakes and engines do not respond instantly.
        self.a_ego += (a_cmd - self.a_ego) * min(1.0, dt / actuator_tau)
        self.v_ego = max(0.0, self.v_ego + self.a_ego * dt)
        self.v_lead = max(0.0, self.v_lead + a_lead * dt)
        self.gap += (self.v_lead - self.v_ego) * dt


@dataclass
class Lateral:
    """Kinematic model: lateral offset y from lane centre and heading error psi."""

    y: float
    psi: float
    v: float

    def step(self, curvature: float, dt: float, road_curvature: float = 0.0) -> None:
        self.psi += self.v * (curvature - road_curvature) * dt
        self.y += self.v * math.sin(self.psi) * dt

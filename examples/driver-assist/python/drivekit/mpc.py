"""Longitudinal model predictive control (MPC) for following a lead vehicle (simulation only).

Every control cycle: predict N steps ahead with a linear model, solve a small
optimization for the best acceleration sequence within limits, apply only the
first acceleration, and repeat next cycle with fresh measurements (receding
horizon). Production systems use dedicated solvers (openpilot uses acados);
here an accelerated projected-gradient solver keeps the maths visible.

The cost has three ingredients: track the driver's set speed, keep the desired
gap to the lead vehicle as a heavily weighted *one-sided* penalty (only being too
close costs anything, like the obstacle constraint in production planners), and
keep acceleration and jerk small. Two details decide whether the car stops in
time for a stationary obstacle: the horizon must be long enough to see the stop
coming (stopping from 25 m/s at comfort braking takes about 7 s), and the lead
must not be a symmetric target — a cost that also rewards closing the gap pulls
the car *toward* a stopped vehicle until it is too late.
"""

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class FollowMPC:
    horizon: int = 40  # steps; 40 x 0.25 s = 10 s
    dt: float = 0.25  # prediction step in seconds
    min_gap: float = 4.0  # metres at standstill
    time_gap: float = 1.5  # seconds of headway at speed
    a_min: float = -3.5  # m/s^2 (comfort braking limit)
    a_max: float = 2.0
    v_set: float = 30.0  # driver's set speed in m/s; the car never tries to exceed it
    w_safe: float = 200.0  # one-sided: heavily penalize a predicted gap below the desired one
    w_speed: float = 0.5  # track the set speed
    w_accel: float = 2.0
    w_jerk: float = 50.0
    iterations: int = 400
    max_jerk: float = 4.0  # m/s^3, hard limit applied to the command after optimizing
    control_dt: float = 0.1  # how often step() is called

    def _matrices(self):
        n, dt = self.horizon, self.dt
        # v_k = v0 + dt * sum_{j<k} a_j        (k = 1..n)
        Av = np.tril(np.ones((n, n))) * dt
        # d_k = d0 + dt * sum_{i<k} (v_lead - v_i), v_0 = v0
        Ad = np.zeros((n, n))
        for k in range(1, n + 1):
            for i in range(1, k):  # v_i depends on a_0..a_{i-1}
                Ad[k - 1, :i] -= dt * dt
        return Av, Ad

    def solve(self, gap: float, v_ego: float, v_lead: float, a_prev: float = 0.0, v_set: float | None = None) -> np.ndarray:
        n, dt = self.horizon, self.dt
        v_set = self.v_set if v_set is None else v_set
        Av, Ad = self._matrices()
        k = np.arange(1, n + 1)
        v_free = np.full(n, v_ego)  # speeds with zero acceleration
        d_free = gap + dt * k * (v_lead - v_ego)
        # Residual blocks, each "constant + M @ a"; cost = 0.5 * sum of weighted squares.
        D = np.eye(n) - np.eye(n, k=-1)  # first differences (jerk)
        e0 = np.zeros(n)
        e0[0] = -a_prev
        gap_const = d_free - (self.min_gap + self.time_gap * v_free)  # predicted gap minus desired gap
        gap_map = Ad - self.time_gap * Av
        blocks = [
            (np.sqrt(self.w_speed), v_free - v_set, Av),
            (np.sqrt(self.w_accel), np.zeros(n), np.eye(n)),
            (np.sqrt(self.w_jerk), e0, D),
        ]
        M = np.vstack([w * m for w, _, m in blocks])
        c = np.concatenate([w * c for w, c, _ in blocks])
        H = M.T @ M
        g = M.T @ c
        # Safety term 0.5 * w_safe * sum(max(0, desired_gap - predicted_gap)^2): zero while the plan
        # keeps the desired gap, so it only acts when a collision course is predicted.
        L = np.linalg.eigvalsh(H).max() + self.w_safe * np.linalg.eigvalsh(gap_map.T @ gap_map).max()
        a = np.clip(np.full(n, a_prev), self.a_min, self.a_max)
        y, t = a.copy(), 1.0
        for _ in range(self.iterations):  # FISTA: projected gradient with momentum
            shortfall = np.maximum(0.0, -(gap_const + gap_map @ y))
            grad = H @ y + g - self.w_safe * (gap_map.T @ shortfall)
            a_next = np.clip(y - grad / L, self.a_min, self.a_max)
            t_next = (1.0 + math.sqrt(1.0 + 4.0 * t * t)) / 2.0
            y = a_next + ((t - 1.0) / t_next) * (a_next - a)
            a, t = a_next, t_next
        return a

    def step(self, gap: float, v_ego: float, v_lead: float, a_prev: float = 0.0, v_set: float | None = None) -> float:
        """Acceleration command for this cycle: first element of the plan, rate-limited.

        The jerk weight in the cost only *discourages* abrupt changes; the rate limit
        *guarantees* a bound, as production controllers do on their outputs.
        Non-finite inputs raise ValueError: the caller must treat that as a fault.
        """
        if not all(math.isfinite(x) for x in (gap, v_ego, v_lead, a_prev)):
            raise ValueError("non-finite input: treat as a fault and disengage")
        a = float(self.solve(gap, v_ego, v_lead, a_prev, v_set)[0])
        max_step = self.max_jerk * self.control_dt
        return min(a_prev + max_step, max(a_prev - max_step, a))

"""Longitudinal model predictive control (MPC) for following a lead vehicle.

Every control cycle: predict N steps ahead with a linear model, solve a small
quadratic program for the best acceleration sequence within limits, apply only
the first acceleration, and repeat next cycle with fresh measurements
(receding horizon). Production systems use dedicated solvers (openpilot uses
acados); here a projected-gradient solver keeps the maths visible.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class FollowMPC:
    horizon: int = 20
    dt: float = 0.2
    min_gap: float = 4.0  # metres at standstill
    time_gap: float = 1.5  # seconds of headway at speed
    a_min: float = -3.5  # m/s^2 (comfort braking limit)
    a_max: float = 2.0
    w_gap: float = 1.0
    w_speed: float = 0.5
    w_accel: float = 2.0
    w_jerk: float = 50.0
    iterations: int = 300
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

    def solve(self, gap: float, v_ego: float, v_lead: float, a_prev: float = 0.0) -> np.ndarray:
        n, dt = self.horizon, self.dt
        Av, Ad = self._matrices()
        k = np.arange(1, n + 1)
        v_free = np.full(n, v_ego)  # speeds with zero acceleration
        d_free = gap + dt * k * (v_lead - v_ego)
        # Residual blocks, each "constant + M @ a"; cost = sum of weighted squares.
        D = np.eye(n) - np.eye(n, k=-1)  # first differences (jerk)
        e0 = np.zeros(n)
        e0[0] = -a_prev
        blocks = [
            (np.sqrt(self.w_gap), d_free - (self.min_gap + self.time_gap * v_free), Ad - self.time_gap * Av),
            (np.sqrt(self.w_speed), v_free - v_lead, Av),
            (np.sqrt(self.w_accel), np.zeros(n), np.eye(n)),
            (np.sqrt(self.w_jerk), e0, D),
        ]
        M = np.vstack([w * m for w, _, m in blocks])
        c = np.concatenate([w * c for w, c, _ in blocks])
        H = M.T @ M
        g = M.T @ c
        step = 1.0 / np.linalg.eigvalsh(H).max()
        a = np.clip(np.full(n, a_prev), self.a_min, self.a_max)
        for _ in range(self.iterations):  # projected gradient: step, then clip into the box
            a = np.clip(a - step * (H @ a + g), self.a_min, self.a_max)
        return a

    def step(self, gap: float, v_ego: float, v_lead: float, a_prev: float = 0.0) -> float:
        """Acceleration command for this cycle: first element of the plan, rate-limited.

        The jerk weight in the cost only *discourages* abrupt changes; the rate limit
        *guarantees* a bound, as production controllers do on their outputs.
        """
        a = float(self.solve(gap, v_ego, v_lead, a_prev)[0])
        max_step = self.max_jerk * self.control_dt
        return min(a_prev + max_step, max(a_prev - max_step, a))

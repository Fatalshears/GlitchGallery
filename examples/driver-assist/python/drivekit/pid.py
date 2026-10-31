"""PID controller with feedforward, output limits and anti-windup."""

from dataclasses import dataclass, field


@dataclass
class PID:
    kp: float
    ki: float = 0.0
    kd: float = 0.0
    kf: float = 0.0  # feedforward gain
    out_min: float = -1.0
    out_max: float = 1.0
    rate_hz: float = 100.0
    _i: float = field(default=0.0, init=False)
    _last_measurement: float | None = field(default=None, init=False)

    def reset(self) -> None:
        self._i, self._last_measurement = 0.0, None

    def update(self, setpoint: float, measurement: float, feedforward: float = 0.0, freeze_integrator: bool = False) -> float:
        dt = 1.0 / self.rate_hz
        error = setpoint - measurement
        # Derivative on measurement (not on error) avoids a kick when the setpoint jumps.
        d = 0.0 if self._last_measurement is None else -(measurement - self._last_measurement) / dt
        self._last_measurement = measurement

        p_term, d_term, f_term = self.kp * error, self.kd * d, self.kf * feedforward
        i_candidate = self._i + self.ki * error * dt
        unclamped = p_term + i_candidate + d_term + f_term
        # Anti-windup (conditional integration): only accept the new integral if the
        # output is not saturated in the direction the integral is pushing.
        saturated_high = unclamped > self.out_max and error > 0
        saturated_low = unclamped < self.out_min and error < 0
        if not (freeze_integrator or saturated_high or saturated_low):
            self._i = i_candidate
        out = p_term + self._i + d_term + f_term
        return min(self.out_max, max(self.out_min, out))

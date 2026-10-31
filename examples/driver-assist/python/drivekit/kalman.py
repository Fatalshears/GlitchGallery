"""Linear Kalman filter and a constant-velocity model for tracking a lead car."""

import numpy as np


class KalmanFilter:
    def __init__(self, x0, P0, F, Q, H, R):
        self.x = np.asarray(x0, float).reshape(-1)
        self.P = np.asarray(P0, float)
        self.F, self.Q, self.H, self.R = (np.asarray(m, float) for m in (F, Q, H, R))

    def predict(self) -> None:
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, z) -> np.ndarray:
        z = np.atleast_1d(np.asarray(z, float))
        y = z - self.H @ self.x  # innovation
        S = self.H @ self.P @ self.H.T + self.R  # innovation covariance
        K = self.P @ self.H.T @ np.linalg.inv(S)  # Kalman gain
        self.x = self.x + K @ y
        # Joseph form keeps P symmetric positive semi-definite despite rounding.
        I_KH = np.eye(len(self.x)) - K @ self.H
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R @ K.T
        return y


def constant_velocity(dt: float, accel_std: float, meas_std: float, x0=(0.0, 0.0)) -> KalmanFilter:
    """State [distance, relative speed]; measures distance only (like a radar range)."""
    F = [[1, dt], [0, 1]]
    G = np.array([[0.5 * dt * dt], [dt]])
    Q = G @ G.T * accel_std**2  # white-noise acceleration model
    return KalmanFilter(x0, np.diag([100.0, 100.0]), F, Q, [[1, 0]], [[meas_std**2]])

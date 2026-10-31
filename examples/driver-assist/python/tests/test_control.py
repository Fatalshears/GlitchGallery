import numpy as np
import pytest

from drivekit.kalman import constant_velocity
from drivekit.mpc import FollowMPC
from drivekit.pid import PID
from drivekit.sim import Lateral, Longitudinal


def first_order_plant(pid, setpoint, steps, disturbance=0.0, tau=0.5, dt=0.01):
    y, ys, us = 0.0, [], []
    for _ in range(steps):
        u = pid.update(setpoint, y)
        y += (u + disturbance - y) * dt / tau
        ys.append(y); us.append(u)
    return np.array(ys), np.array(us)


def test_p_only_leaves_steady_state_error_integral_removes_it():
    ys, _ = first_order_plant(PID(kp=2.0, out_min=-10, out_max=10), 1.0, 2000, disturbance=-0.5)
    assert abs(1.0 - ys[-1]) > 0.1  # P alone settles short of the target
    ys, _ = first_order_plant(PID(kp=2.0, ki=2.0, out_min=-10, out_max=10), 1.0, 2000, disturbance=-0.5)
    assert ys[-1] == pytest.approx(1.0, abs=0.01)


def test_anti_windup_recovers_faster_than_naive():
    def run(pid):
        # Long saturation phase (unreachable setpoint), then a reachable one.
        y = 0.0
        for _ in range(1000):
            u = pid.update(5.0, y); y += (u - y) * 0.01 / 0.5
        for k in range(3000):
            u = pid.update(0.5, y); y += (u - y) * 0.01 / 0.5
            if abs(y - 0.5) < 0.05:
                return k
        return 3000
    good = run(PID(kp=1.0, ki=2.0, out_min=-1, out_max=1))

    class Naive(PID):  # always integrates
        def update(self, setpoint, measurement, feedforward=0.0, freeze_integrator=False):
            self._i += self.ki * (setpoint - measurement) / self.rate_hz
            return min(self.out_max, max(self.out_min, self.kp * (setpoint - measurement) + self._i))
    naive = run(Naive(kp=1.0, ki=2.0, out_min=-1, out_max=1))
    assert good < naive / 3


def test_derivative_on_measurement_has_no_setpoint_kick():
    pid = PID(kp=0.0, kd=1.0, out_min=-100, out_max=100)
    pid.update(0.0, 0.0)
    assert pid.update(10.0, 0.0) == 0.0  # setpoint jump, measurement unchanged: no D spike


def test_kalman_estimates_relative_speed_from_noisy_range():
    rng = np.random.default_rng(0)
    kf = constant_velocity(dt=0.05, accel_std=0.5, meas_std=1.0, x0=(60.0, 0.0))
    true_d, true_v = 60.0, -2.0  # closing in from 60 m to 20 m
    innovations = []
    for _ in range(400):  # 20 s at 20 Hz
        true_d += true_v * 0.05
        kf.predict()
        innovations.append(kf.update(true_d + rng.normal(0, 1.0))[0])
    assert kf.x[1] == pytest.approx(true_v, abs=0.3)
    assert kf.x[0] == pytest.approx(true_d, abs=1.0)
    assert np.allclose(kf.P, kf.P.T) and np.all(np.linalg.eigvalsh(kf.P) > 0)
    assert abs(np.mean(innovations[100:])) < 0.2  # unbiased once converged


def drive(lead_accel, seconds=30.0, gap=50.0, v=25.0, v_lead=25.0):
    mpc, dt = FollowMPC(), 0.1
    car = Longitudinal(gap=gap, v_ego=v, v_lead=v_lead)
    a_cmd, trace = 0.0, []
    for i in range(int(seconds / dt)):
        a_cmd = mpc.step(car.gap, car.v_ego, car.v_lead, a_prev=a_cmd)
        car.step(a_cmd, lead_accel(i * dt), dt)
        trace.append((car.gap, car.v_ego, a_cmd))
    return np.array(trace)


def test_mpc_follows_braking_lead_without_collision():
    tr = drive(lambda t: -3.0 if 2.0 <= t < 7.0 else 0.0)  # lead slows 25 -> 10 m/s
    gaps, speeds, accels = tr[:, 0], tr[:, 1], tr[:, 2]
    assert gaps.min() > 4.0
    assert accels.min() >= -3.5 - 1e-9 and accels.max() <= 2.0 + 1e-9
    assert (np.abs(np.diff(accels)) / 0.1).max() <= 4.0 + 1e-9
    assert speeds[-1] == pytest.approx(10.0, abs=0.5)
    assert gaps[-1] == pytest.approx(4.0 + 1.5 * 10.0, abs=2.5)  # min gap + time gap × speed


def test_mpc_closes_a_large_gap_smoothly():
    tr = drive(lambda t: 0.0, seconds=40.0, gap=120.0, v=20.0, v_lead=25.0)
    jerk = np.abs(np.diff(tr[:, 2])) / 0.1
    assert tr[-1, 1] == pytest.approx(25.0, abs=0.5)
    assert jerk.max() <= 4.0 + 1e-9  # m/s^3: the hard jerk limit holds


def test_lane_centering_converges_without_large_overshoot():
    car = Lateral(y=1.0, psi=0.0, v=20.0)
    pid = PID(kp=0.004, ki=0.0005, kd=0.004, out_min=-0.02, out_max=0.02, rate_hz=20)
    ys = []
    for _ in range(400):  # 20 s at 20 Hz
        curvature = pid.update(0.0, car.y)
        car.step(curvature, 0.05)
        ys.append(car.y)
    ys = np.array(ys)
    assert abs(ys[-1]) < 0.05
    assert ys.min() > -0.3  # overshoot below 30 cm

---
title: Control and Estimation in Python
type: cookbook
tags: [cookbook, python, control-theory, numpy]
aliases: [numpy control loop, simulate controller python, scipy signal, kalman filter numpy]
versions: "Python 3.10+, NumPy 1.24+, SciPy 1.10+ (checked with NumPy 2.x, SciPy 1.18)"
status: draft
levels: [2, 3]
---

Concepts: [[pid-controller]] · [[model-predictive-control]] · [[kalman-filter]] · [[fixed-rate-control-loops]].

Python is the usual language for designing, simulating and tuning controllers — and openpilot runs much of its planning and control in Python on the car. The pattern is always: **model the plant, close the loop in simulation, assert on the behaviour, then plot.**

## API map

| Need | API |
|---|---|
| Discrete simulation loop | plain Python + NumPy state arrays |
| Linear systems, step responses | `scipy.signal.StateSpace`, `scipy.signal.dlsim`, `python-control` |
| Discretize a continuous model | `scipy.signal.cont2discrete((A, B, C, D), dt)` |
| Solve least squares / QPs | `np.linalg.lstsq`, `scipy.optimize.minimize(..., bounds=)`, `osqp`, `cvxpy` |
| Matrix ops for Kalman filters | `@`, `np.linalg.inv` / `solve`, `np.linalg.eigvalsh` |
| Plot | `matplotlib.pyplot.plot`, PlotJuggler for logs |

## Recipes

> [!mwe] Discretize a continuous model and check a step response
> - **Used for:** Getting a correct discrete model `x[k+1] = Ad x[k] + Bd u[k]` for a 100 Hz controller instead of guessing.
> - **Input:** A first-order actuator with time constant 0.3 s: `dx/dt = (u − x) / 0.3`.
> - **Expected output:** `Ad ≈ 0.9672`, `Bd ≈ 0.0328`; after 1 s of a unit step the output is `≈ 0.9643` (= 1 − e^(−1/0.3)).
>
> ```python
> import numpy as np
> from scipy.signal import cont2discrete, dlsim
>
> tau, dt = 0.3, 0.01
> Ad, Bd, Cd, Dd, _ = cont2discrete((np.array([[-1 / tau]]), np.array([[1 / tau]]), np.eye(1), np.zeros((1, 1))), dt)
> t, y, _ = dlsim((Ad, Bd, Cd, Dd, dt), np.ones(101))
> print(Ad.item().__round__(4), Bd.item().__round__(4), y[100].item().__round__(4))
> ```

> [!mwe] Closed-loop scenario test pattern
> - **Used for:** Turning "the controller seems fine" into assertions that run in CI.
> - **Input:** Any controller with `step(observation) -> command` and a plant simulator.
> - **Expected output:** The test passes only if every safety and comfort property holds over the whole run; a failure message names the first violated property and time.
>
> ```python
> def check_run(trace, dt, min_gap=4.0, a_lim=(-3.5, 2.0), max_jerk=4.0):
>     for i, (gap, v, a) in enumerate(trace):
>         assert gap > min_gap, f"t={i*dt:.1f}s gap {gap:.2f} m"
>         assert a_lim[0] <= a <= a_lim[1], f"t={i*dt:.1f}s accel {a:.2f}"
>         if i:
>             jerk = abs(a - trace[i - 1][2]) / dt
>             assert jerk <= max_jerk + 1e-9, f"t={i*dt:.1f}s jerk {jerk:.2f}"
> ```

> [!tested] Full reference — `examples/driver-assist/python` (`drivekit`)
> - **Used for:** PID, Kalman filter, MPC, simulators and replay tests working together.
> - **Input:** Python 3.10+ with numpy and pytest.
> - **Expected output:** `31 passed` (about 30 s).
>
> ```bash
> cd examples/driver-assist/python
> python -m pip install numpy pytest
> python -m pytest -q
> ```

## Gotchas

- Euler discretization (`x += f(x)·dt`) is fine for small dt but unstable for stiff systems — use `cont2discrete` or smaller steps.
- Python loops at 100 Hz are fine; vectorize the inner maths when a planner solves many steps per cycle.
- `np.linalg.inv` in Kalman updates is fine for 2×2; prefer `np.linalg.solve` for larger systems.
- Floating-point results differ slightly across machines and NumPy versions — compare with tolerances in replay tests.
- Never use wall-clock `time.time()` inside simulations — pass `dt` explicitly so tests are deterministic.

## References

- SciPy `signal` — https://docs.scipy.org/doc/scipy/reference/signal.html
- `python-control` — https://python-control.readthedocs.io/
- Labbe, *Kalman and Bayesian Filters in Python* — https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python

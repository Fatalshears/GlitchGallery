---
title: Model Predictive Control
type: concept
domain: control
tags: [concept, control-theory, optimization, robotics]
aliases: [MPC, receding horizon control, optimal control, quadratic program]
status: draft
levels: [1, 2, 3]
---

## Problem and purpose

Some control tasks need to **look ahead** and respect **constraints**: brake early for a slowing car, never exceed comfort limits, keep a minimum gap. **Model predictive control (MPC)** uses a model to predict the system's future, solves an optimization for the best input sequence under limits, applies only the first input, and repeats every cycle. It is used in vehicle planners (openpilot's longitudinal planner), chemical plants, drones, building climate control and walking robots.

## Core concepts and terminology

- **Prediction model** — e.g. `v[k+1] = v[k] + a[k]·dt`, `gap[k+1] = gap[k] + (v_lead − v[k])·dt`.
- **Horizon** — how many steps ahead are planned (N × dt seconds).
- **Cost function** — weighted sum of squared errors (gap, speed) and effort (acceleration, jerk).
- **Constraints** — hard bounds such as `a_min ≤ a ≤ a_max`.
- **Quadratic program (QP)** — linear model + quadratic cost + linear constraints; solvable fast and reliably.
- **Receding horizon** — re-solve each cycle with new measurements; only the first action is applied.
- **Soft vs hard limits** — penalties in the cost vs constraints/rate limiters that are guaranteed.

*Search keywords:* `model predictive control tutorial`, `receding horizon`, `quadratic program box constraints`, `acados`, `OSQP`, `MPC horizon tuning`.

## How it works

```mermaid
sequenceDiagram
  participant S as Sensors
  participant M as MPC
  participant A as Actuator
  loop every control cycle (e.g. 10 Hz)
    S->>M: gap, v_ego, v_lead
    M->>M: predict N steps for candidate accelerations
    M->>M: minimise cost subject to limits (QP)
    M->>A: apply first acceleration only
  end
```

> [!pseudocode] One MPC step with a projected-gradient QP solver
> - **Used for:** Showing the full loop without a solver library.
> - **Input:** Current state; matrices `M, c` such that every weighted cost residual is `c + M·a`; box limits.
> - **Expected output:** A feasible acceleration sequence `a` (within limits) that minimises `||c + M·a||²`; its first element is applied.
>
> ```
> H = Mᵀ M ;  g = Mᵀ c            # cost = ½ aᵀ H a + gᵀ a + const
> step = 1 / largest_eigenvalue(H)
> a = clip(previous_plan, a_min, a_max)
> repeat K times:
>     a = clip(a − step · (H a + g), a_min, a_max)    # gradient step, then project into the box
> return a[0]
> ```

## Related features and components

[[adaptive-cruise-control]] · [[pid-controller]] (simpler, reactive alternative) · [[kalman-filter]] (provides the state MPC starts from) · [[fixed-rate-control-loops]] (solver time must fit the cycle).

## Required technical knowledge

Linear algebra (matrices, least squares), basic optimization (gradients, constraints), [[pid-controller]].

## Implementation techniques and APIs

> [!tested] Python — `drivekit/mpc.py`
> - **Used for:** Following a lead vehicle with acceleration limits, comfort costs and a hard jerk limit.
> - **Input:** Gap, ego speed, lead speed, previous acceleration; tuning in `FollowMPC` (horizon 20 × 0.2 s, time gap 1.5 s, limits −3.5…+2 m/s², jerk ≤ 4 m/s³).
> - **Expected output:** An acceleration command each call. In closed loop with a lead braking from 25 to 10 m/s, the gap never drops below 4 m and settles near 19 m; closing a 120 m gap at +5 m/s relative speed ends matched to the lead's speed with jerk within 4 m/s³.
>
> ```python
> from drivekit.mpc import FollowMPC
> mpc = FollowMPC()
> plan = mpc.solve(gap=30.0, v_ego=25.0, v_lead=20.0)   # 20 planned accelerations
> a_cmd = mpc.step(gap=30.0, v_ego=25.0, v_lead=20.0)   # first one, jerk-limited from a_prev=0
> ```
> Tests: `test_mpc_follows_braking_lead_without_collision`, `test_mpc_closes_a_large_gap_smoothly`, plus the process-replay reference test.

Solvers in practice: **acados** (openpilot's choice; generates C code), **OSQP**, **CasADi**, `cvxpy` for prototyping.

## Error handling and edge cases

- **Infeasibility** (no input satisfies all constraints, e.g. a sudden cut-in): use soft constraints with large penalties and fall back to maximum safe braking.
- **Solver time overruns** — warm-start from the previous plan, cap iterations, and keep a safe fallback command.
- **Model mismatch** (actuator lag, slopes) — re-planning every cycle corrects much of it; model the lag if it is large.

## Testing and debugging

- Closed-loop scenario tests with assertions on constraints and comfort (jerk) — in drivekit they revealed that the jerk *cost* alone allowed 6 m/s³ peaks, which is why a hard rate limit was added.
- Plot the whole predicted plan each cycle, not just the applied command.

## Limitations and engineering trade-offs

- Longer horizons see further but cost more computation; in drivekit's tests, extending from 4 s to 8 s barely changed peak jerk — weights and limits mattered more.
- Weight tuning trades comfort against tracking; hard limits should be enforced outside the cost.
- Nonlinear models (lateral dynamics at the limit) need nonlinear MPC — much harder.

## Competency checklist

> [!level1] Recognition
> Explain horizon, cost, constraints, QP and receding horizon; contrast MPC with PID.

> [!level2] Implementation
> Formulate a linear MPC with box constraints, solve it (projected gradient or OSQP) and pass closed-loop tests.

> [!level3] Engineering
> Handle infeasibility, real-time solver budgets, warm starts, model mismatch and tuning with recorded data.

## References

- Rawlings, Mayne & Diehl, *Model Predictive Control: Theory, Computation, and Design* (free PDF from the authors).
- acados — https://docs.acados.org/
- OSQP — https://osqp.org/
- openpilot longitudinal MPC — https://github.com/commaai/openpilot/tree/master/selfdrive/controls/lib/longitudinal_mpc_lib

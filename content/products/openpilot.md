---
title: openpilot
type: product
tags: [product, robotics, automotive, safety, python, cpp]
aliases: [comma openpilot, driver assistance, ADAS, comma.ai]
status: draft
---

> [!danger] Educational content only
> This slice explains how driver-assistance software works. The example code in this wiki is a learning aid: it has never been validated for any vehicle and must never be connected to one. Real systems rely on independent hardware safety layers, formal safety processes and millions of kilometres of testing.

## Purpose

openpilot is an open-source **advanced driver-assistance system (ADAS)** from comma.ai (open-sourced in 2016, MIT licence). It runs on a dashboard-mounted device (currently the comma 3X) that plugs into a supported car's internal network and provides **adaptive cruise control** and **automated lane centering** on hundreds of car models, replacing or upgrading the car's stock assistance. It is an SAE **Level 2** system: it steers, accelerates and brakes, but the driver must watch the road at all times, and a camera-based **driver monitor** enforces that.

Most of the code is **Python** (planning, control, process orchestration, tools), with **C/C++** where timing or safety demands it (camera and sensor daemons, messaging, the panda's safety firmware in C).

## Users and pain points

| User situation | Pain without it | What openpilot does about it |
|---|---|---|
| Long highway drives, stop-and-go traffic | Constant speed adjustments are tiring | Keeps a safe following distance automatically — [[adaptive-cruise-control]] |
| Holding the lane for hours | Fatigue, drifting | Keeps the car centred in its lane — [[lane-centering]] |
| Assistance that lulls drivers into inattention | Misuse of Level 2 systems | Camera watches the driver; alerts, then disengages — [[driver-monitoring]] |
| Car's stock system is weak or missing | Hardware already exists but software is limited | Talks to the car's own steering/gas/brake modules over CAN — [[vehicle-integration]] |
| Software controlling a car can have bugs | Unsafe commands could reach the actuators | Separate firmware blocks unsafe commands — [[independent-safety-layer]] |
| Improving behaviour without regressions | Hard to know a change is better | Every drive logged; changes replayed against real data — [[drive-logging-and-replay]] |

## Core features

```mermaid
mindmap
  root((openpilot))
    Driving
      Adaptive cruise control
      Lane centering
    Driver
      Driver monitoring
      Alerts
    Vehicle
      CAN integration
      Car ports and DBC files
    Safety
      Independent safety firmware
      Engagement rules
    Data
      Logging
      Process replay
      Analysis tools
```

## Main workflow

One control cycle while engaged (openpilot's main control loop runs at 100 Hz):

```mermaid
sequenceDiagram
  participant CAM as camerad
  participant MOD as modeld
  participant PLAN as planner
  participant CTRL as controls
  participant CAR as car interface
  participant PANDA as panda (safety firmware)
  participant ECU as car ECUs
  CAM->>MOD: road camera frames (20 Hz)
  MOD->>PLAN: lane lines, path, lead car (neural net)
  ECU->>PANDA: CAN: speed, brake, steering torque
  PANDA->>CAR: CAN frames
  CAR->>CTRL: carState (decoded)
  PLAN->>CTRL: target acceleration and curvature
  CTRL->>CAR: steer torque, accel (100 Hz)
  CAR->>PANDA: CAN frames to send
  PANDA->>PANDA: safety check (rate limits, engagement)
  PANDA->>ECU: forward only if allowed
```

## Feature decomposition

```mermaid
flowchart LR
  subgraph Features
    ACC[Adaptive cruise]
    LC[Lane centering]
    DM[Driver monitoring]
    VI[Vehicle integration]
    SL[Safety layer]
    LR[Logging and replay]
  end
  subgraph Components
    MODEL[Driving model]
    LONG[Longitudinal planner]
    LAT[Lateral controller]
    EST[State estimation]
    CANIO[CAN parser / packer]
    FW[Safety firmware]
    FSM[Engagement state machine]
    MSG[Messaging]
    LOG[Logger + replay]
  end
  ACC --> MODEL & LONG & EST
  LC --> MODEL & LAT
  DM --> MODEL & FSM
  VI --> CANIO
  SL --> FW & FSM
  LR --> LOG & MSG
  LONG --> c1(["Model predictive control"])
  LAT --> c2(["PID controller"])
  EST --> c3(["Kalman filter"])
  MODEL --> c4(["On-device ML inference"])
  CANIO --> c5(["CAN bus"])
  FW --> c6(["Functional safety"])
  MSG --> c7(["Publish/subscribe"]) & c8(["Ring buffer"])
  LOG --> c9(["Record and replay testing"])
  LONG & LAT --> c10(["Fixed-rate control loops"])
```

| Feature | Components | Concepts | Cookbook |
|---|---|---|---|
| [[adaptive-cruise-control]] | longitudinal planner, lead estimation | [[model-predictive-control]], [[kalman-filter]], [[fixed-rate-control-loops]] | [[control-and-estimation-in-python]] |
| [[lane-centering]] | lateral controller | [[pid-controller]], [[coordinate-transforms]], [[on-device-ml-inference]] | [[control-and-estimation-in-python]] |
| [[driver-monitoring]] | monitoring model, alert logic | [[on-device-ml-inference]], [[finite-state-machine]] | — |
| [[vehicle-integration]] | CAN parser/packer, car ports | [[can-bus]] | [[can-bus-in-python]] |
| [[independent-safety-layer]] | safety firmware, engagement rules | [[functional-safety]], [[finite-state-machine]] | [[realtime-cpp]] |
| [[drive-logging-and-replay]] | logger, process replay | [[record-and-replay-testing]], [[publish-subscribe-messaging]], [[ring-buffer]] | [[realtime-cpp]] |

## Architecture sketch

```mermaid
flowchart TB
  subgraph Device["comma device (Linux)"]
    CAMD[camerad] --> MODELD[modeld: driving model]
    CAMD --> DMOD[driver monitoring model]
    MODELD --> PLANNER[planner: longitudinal MPC]
    LOCD[locationd / calibration: Kalman filters] --> PLANNER
    PLANNER --> CONTROLS[controls: lateral + longitudinal, 100 Hz]
    DMOD --> SELF[engagement and alerts]
    SELF --> CONTROLS
    CARD[car interface: CAN parse/pack] <--> CONTROLS
    PANDAD[pandad] <--> CARD
    BUS{{"pub/sub messaging: Cap'n Proto over shared memory"}}
    LOGGERD[loggerd: logs + video] --> UP[uploader]
  end
  PANDA["panda: USB-CAN interface<br/>safety firmware in C"] <--> PANDAD
  CANBUS[(car CAN buses)] <--> PANDA
  UP --> CLOUD[(drive logs in the cloud)]
```

Process names differ between openpilot versions; the structure is what matters. Design points worth noticing:

- **Many small processes, one message bus.** Each daemon does one job and publishes typed messages (schemas in Cap'n Proto, via comma's `cereal` and `msgq` libraries). A crash or slowdown in one is visible to the others through message timestamps and validity flags ([[publish-subscribe-messaging]]).
- **Safety is enforced outside the main computer.** The panda firmware checks every outgoing actuator message against car-specific limits and engagement state, so a bug in Python cannot command an unsafe steering jerk ([[independent-safety-layer]]).
- **Everything is logged.** Inputs and outputs of every process are recorded; changes are tested by replaying real drives through the new code and diffing the outputs ([[drive-logging-and-replay]]).
- **Learn from data, control with classical methods.** A neural network perceives the road; well-understood control (MPC, PID) and estimation (Kalman filters) turn perception into actuator commands with explicit limits.

## Build it yourself

Follow **[[build-a-driver-assist-stack]]**, a simulation-only project: CAN decoding, state estimation, cruise control with MPC, lane centering, an independent safety checker, pub/sub messaging, and record/replay tests. The result is the tested Python reference `examples/driver-assist/python` (`drivekit`) plus C++ twins of the safety checker and the lock-free ring buffer.

## References

- openpilot source (MIT) — https://github.com/commaai/openpilot
- openpilot `docs/SAFETY.md` (safety model) — https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md
- panda (CAN interface and safety firmware) — https://github.com/commaai/panda
- opendbc (DBC files and car interfaces) — https://github.com/commaai/opendbc
- SAE J3016, *Levels of Driving Automation* — https://www.sae.org/standards/content/j3016_202104/

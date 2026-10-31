---
title: CAN Bus in Python (python-can and cantools)
type: cookbook
tags: [cookbook, python, automotive, embedded]
aliases: [python-can, cantools, DBC python, virtual can bus, SocketCAN python]
versions: "Python 3.10+, python-can 4.x, cantools 39+ (checked with python-can 4.6, cantools 45)"
status: draft
levels: [2]
---

Concepts: [[can-bus]] · [[vehicle-integration]] · [[record-and-replay-testing]].

> [!danger] Never transmit on a real vehicle bus while learning
> Use virtual buses and recorded logs. Sending frames to a car can disable its safety systems.

## API map

| Need | API |
|---|---|
| Open a bus | `can.Bus(interface="virtual", channel="test")`; Linux hardware: `interface="socketcan", channel="can0"` |
| Send / receive | `bus.send(can.Message(arbitration_id=..., data=..., is_extended_id=False))`, `bus.recv(timeout=1.0)` |
| Load a DBC | `db = cantools.database.load_file("car.dbc")` or `load_string(text, database_format="dbc")` |
| Decode / encode | `db.decode_message(frame_id, data)`, `db.encode_message(name_or_id, {"SIGNAL": value})` |
| Log / replay | `can.Logger("drive.asc")`, `can.LogReader("drive.asc")`, `can.MessageSync` for timed replay |
| Linux virtual bus | `sudo ip link add dev vcan0 type vcan && sudo ip link set up vcan0`; `candump vcan0` |

## Recipes

> [!mwe] Decode and encode with a DBC, send over a virtual bus
> - **Used for:** The full loop: DBC text → encode a physical value → send → receive on another bus handle → decode.
> - **Input:** `pip install python-can cantools`; the DBC text below (one message with an Intel and a Motorola signal).
> - **Expected output:** `{'VEHICLE_SPEED': 27.78, 'STEER_ANGLE': -12.5}` (the received frame decodes back to the sent values).
>
> ```python
> import can
> import cantools
>
> DBC = """VERSION ""
> BO_ 512 CAR_STATE: 8 ECU
>  SG_ VEHICLE_SPEED : 0|16@1+ (0.01,-50) [-50|605.35] "m/s" XXX
>  SG_ STEER_ANGLE : 23|16@0- (0.1,0) [-3276.8|3276.7] "deg" XXX
> """
> db = cantools.database.load_string(DBC, database_format="dbc")
> data = db.encode_message("CAR_STATE", {"VEHICLE_SPEED": 27.78, "STEER_ANGLE": -12.5})
>
> with can.Bus(interface="virtual", channel="test") as tx, can.Bus(interface="virtual", channel="test") as rx:
>     tx.send(can.Message(arbitration_id=512, data=data, is_extended_id=False))
>     msg = rx.recv(timeout=1.0)
>     print(db.decode_message(msg.arbitration_id, msg.data))
> ```
> In DBC syntax `0|16@1+` means start bit 0, 16 bits, `@1` Intel (little-endian), `+` unsigned; `23|16@0-` is Motorola (big-endian), signed. `(0.01,-50)` is factor and offset.

> [!tested] Same maths without libraries — `drivekit/can.py`
> - **Used for:** Understanding what cantools does internally: bit positions for both byte orders, scale/offset, two's complement.
> - **Input:** None for the tests.
> - **Expected output:** `5 passed` for `tests/test_can.py`, including 1000 random round trips that leave all other bits untouched.
>
> ```bash
> cd examples/driver-assist/python && python -m pytest tests/test_can.py
> ```

## Gotchas

- **Start bit for Motorola signals** is the most significant bit in DBC's "sawtooth" bit numbering — the most common source of garbage values.
- `decode_message` returns choice names for enumerated signals (`"ON"`) unless you pass `decode_choices=False`.
- `encode_message` rejects out-of-range values (`EncodeError`) by default — good; do not disable the check casually.
- Virtual buses with the same `channel` name share frames within one process only; use `vcan` for multi-process tests.
- Frames you receive from a real car arrive on several buses (`bus` field / channel); the same id can mean different things on different buses.

## References

- python-can documentation — https://python-can.readthedocs.io/
- cantools documentation — https://cantools.readthedocs.io/
- DBC format overview — https://www.csselectronics.com/pages/can-dbc-file-database-intro

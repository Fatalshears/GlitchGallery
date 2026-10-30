---
title: Field Notes
type: hub
---

Short write-ups of real failures met in practice: symptoms, root cause, fix, and how to diagnose it next time. They complement the concept pages — a field note is a concrete story, a concept page is the general rule.

| Note | Symptom | Concepts involved |
|---|---|---|
| [[windows-console-server-freeze]] | server stalls for all clients when someone clicks its console window | [[producer-consumer-queue]] (queued logging), blocking I/O on the request thread ([[async-io-event-loop]]) |
| [[claude-code-model-access-litellm]] | Claude Code works through LiteLLM in Anthropic mode but not in Vertex mode | API gateways and protocol translation |

To add one, follow the field-note format in [[contributing]].

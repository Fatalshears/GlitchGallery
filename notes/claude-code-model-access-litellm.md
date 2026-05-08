# Why Claude Code Vertex Mode Fails Through LiteLLM but Anthropic Mode Works

## Setup Context

A LiteLLM proxy runs on the intranet as an LLM gateway. Claude Code on a client machine connects to it over LAN.

The intended flow is:

```
Claude Code
    ↓
LiteLLM Gateway
    ↓
Vertex Backend / Model Farm
```

The expectation is that LiteLLM transparently bridges Claude Code requests to a real Vertex AI backend. This works when Claude Code is in Anthropic API mode. It does not work when Claude Code is in Vertex mode.

---

## Configuration A — Vertex Mode via LiteLLM Gateway (FAILS)

```bash
ANTHROPIC_API_KEY=<virtual-key>
ANTHROPIC_VERTEX_BASE_URL=http://<proxy-host>:4000
CLAUDE_CODE_USE_VERTEX=1
CLOUD_ML_REGION=_
ANTHROPIC_VERTEX_PROJECT_ID=_
CLAUDE_CODE_SKIP_VERTEX_AUTH=1
```

### Why it fails

**The fundamental problem: Claude Code Vertex mode expects the first hop to behave like a real Vertex AI deployment.**

Setting `CLAUDE_CODE_USE_VERTEX=1` does not simply change the base URL. It switches Claude Code into a provider-specific Vertex AI client mode. Even with `CLAUDE_CODE_SKIP_VERTEX_AUTH=1` disabling GCP authentication flows, Claude Code still operates with the full set of Vertex-oriented behaviours:

- Vertex-specific startup and capability probing
- Vertex model resolution and availability checks
- Vertex-style request routing and URL construction
- Vertex-compatible model ID semantics
- Vertex response contract validation

`CLAUDE_CODE_SKIP_VERTEX_AUTH=1` only removes the Google credential layer. It does **not** convert Claude Code into a generic HTTP client — all Vertex protocol assumptions remain active.

LiteLLM is a provider-routing gateway, not a Vertex AI emulator. It does not reproduce the complete external Vertex API surface that Claude Code Vertex mode expects. Pointing Vertex-mode Claude Code at LiteLLM is asking LiteLLM to *be* Vertex — not merely to *route to* Vertex.

---

**Problem 1 — Vertex capability probing fails with stub project/region**

The placeholder values:

```bash
CLOUD_ML_REGION=_
ANTHROPIC_VERTEX_PROJECT_ID=_
```

are not treated as ignored metadata. Claude Code Vertex mode uses the project and region during Vertex initialization and model discovery. With invalid values, capability probing fails, producing errors such as:

```
The model claude-sonnet-4-6 is not available on your vertex deployment
```

This is not a static client-side model blocklist. It is Vertex-specific capability validation failing because the configured project/region context is structurally invalid.

---

**Problem 2 — Vertex request paths are not natively handled by LiteLLM**

Vertex mode constructs requests using Vertex-style routes:

```
POST /v1/projects/{project}/locations/{region}/publishers/anthropic/models/{model}:rawPredict
```

LiteLLM natively exposes Anthropic-compatible endpoints (`POST /v1/messages`). It does not fully emulate the complete external Vertex API contract. A custom route shim can partially forward requests, but this is not equivalent to a real Vertex deployment.

---

**Problem 3 — Vertex model IDs differ from Anthropic API model names**

Vertex AI uses publisher-managed versioned model identifiers:

```
claude-sonnet-4-5@20250929
claude-haiku-4-5@20251001
```

Anthropic API mode uses short aliases:

```
claude-sonnet-4-6
claude-opus-4-6
```

Claude Code Vertex mode expects Vertex-compatible model naming semantics. Anthropic API aliases do not map cleanly onto Vertex publisher IDs and will fail Vertex model resolution.

---

## Configuration B — Anthropic API Mode via LiteLLM Gateway (WORKS)

```bash
ANTHROPIC_AUTH_TOKEN=<virtual-key>
ANTHROPIC_BASE_URL=http://<proxy-host>:4000
```

### Why it works

In Anthropic API mode, Claude Code operates as a generic Anthropic-compatible API client. No Vertex-specific initialization occurs — no GCP project validation, no Vertex capability probing, no Vertex URL construction.

| Component | Behaviour |
|---|---|
| Client mode | Generic Anthropic-compatible API client |
| URL pattern | `POST /v1/messages` — natively handled by LiteLLM |
| Authentication | `ANTHROPIC_AUTH_TOKEN` sent as `x-api-key` header |
| Model handling | Model name passed directly to server as-is |
| Vertex semantics required | None |

LiteLLM is designed specifically for this kind of proxying workflow. Claude Code sends standard Anthropic-compatible requests; LiteLLM routes them to the appropriate backend (e.g. a Vertex adapter or model farm). No protocol mismatch exists.

---

## Architectural Difference

**Working path — LiteLLM in its intended role:**

```
Claude Code (Anthropic API mode)
    ↓  POST /v1/messages
LiteLLM Gateway  (provider-agnostic router)
    ↓
Backend Adapter → Vertex / Model Farm
```

**Failing path — LiteLLM asked to impersonate Vertex:**

```
Claude Code (Vertex mode)
    ↓  POST /v1/projects/.../models/{model}:rawPredict
LiteLLM Gateway  (not a Vertex AI deployment)
    ↓
Backend Adapter → Vertex / Model Farm
```

In the failing path, Claude Code expects the first hop to satisfy the full Vertex AI protocol contract. LiteLLM does not and cannot — it is a routing gateway, not a Vertex replica.

---

## Summary

| Factor | Vertex Mode via LiteLLM | Anthropic API Mode via LiteLLM |
|---|---|---|
| Intended target | Real Vertex AI deployment | Anthropic-compatible API |
| Client mode | Vertex-specific, full Vertex protocol | Generic, provider-agnostic |
| `SKIP_VERTEX_AUTH` effect | Removes GCP auth only — Vertex protocol remains | N/A |
| Startup validation | Vertex capability probing with project/region | Minimal |
| URL format | Vertex API routes (`:rawPredict`) | `/v1/messages` |
| Model naming | Requires `@`-versioned Vertex publisher IDs | Accepts any alias |
| LiteLLM compatibility | Structural mismatch — LiteLLM is not a Vertex emulator | Native |
| Works reliably | ❌ | ✅ |

---

## Bottom Line

`CLAUDE_CODE_USE_VERTEX=1` makes Claude Code speak Vertex AI — not just point at a different URL. `CLAUDE_CODE_SKIP_VERTEX_AUTH=1` strips only the GCP authentication layer; all other Vertex protocol behaviour remains.

LiteLLM is designed to be a provider-routing gateway, not a full external Vertex AI emulator. Asking Claude Code Vertex mode to target LiteLLM creates a fundamental protocol mismatch at the first hop.

Anthropic API mode avoids all Vertex-specific assumptions entirely. Claude Code sends standard Anthropic API requests, LiteLLM routes them natively, and the proxy fulfils its intended role without any protocol mismatch.

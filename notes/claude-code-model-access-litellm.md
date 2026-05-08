# Why Claude Code + LiteLLM Gateway: Vertex Mode Fails, Anthropic Mode Works

## Setup Context

A LiteLLM proxy runs on the intranet, acting as a gateway that routes AI API calls to a backend model farm. Claude Code on a client machine connects to it over LAN.

---

## Configuration A — Vertex Mode (does NOT work)

```
ANTHROPIC_API_KEY=<virtual-key>
ANTHROPIC_VERTEX_BASE_URL=http://<proxy-host>:4000
CLAUDE_CODE_USE_VERTEX=1
CLOUD_ML_REGION=_
ANTHROPIC_VERTEX_PROJECT_ID=_
CLAUDE_CODE_SKIP_VERTEX_AUTH=1
```

### Why it fails

**Problem 1 — Startup model availability check fails against stub credentials (root cause)**

When `CLAUDE_CODE_USE_VERTEX=1` is set, Claude Code switches into Vertex AI mode. On startup, it performs a model availability check — it probes the configured Vertex endpoint to verify that the models it intends to use are actually accessible in the given project and region.

Using `_` as placeholder values for `ANTHROPIC_VERTEX_PROJECT_ID` and `CLOUD_ML_REGION` means this probe goes to a structurally invalid GCP endpoint. The check fails, producing errors like:

```
The model claude-sonnet-4-6 is not available on your vertex deployment
```

This is not a hardcoded client-side list of allowed model names. It is a runtime availability probe that fails because the project/region values are invalid stubs. Newer model names (e.g. `claude-sonnet-4-6`) may also be rejected because they lack the `@`-versioned suffix format that Vertex AI requires (e.g. `claude-sonnet-4-6@20250514`) — the Anthropic API short-name format is not valid as a Vertex model ID.

> **Note:** `CLAUDE_CODE_SKIP_VERTEX_AUTH=1` is not an officially documented Claude Code environment variable. Its behaviour may be undocumented, version-specific, or unreliable. Do not rely on it for production configurations.

**Problem 2 — Vertex URL path mismatch**

Vertex mode sends requests using the Vertex AI URL pattern:

```
POST /v1/projects/{project}/locations/{region}/publishers/anthropic/models/{model}:rawPredict
```

LiteLLM does have native Vertex AI support, but it expects to handle GCP authentication itself — it is not designed to act as a transparent pass-through for Vertex-formatted requests arriving from an external client. The custom handler added to `proxy_app.py` is a workaround for this mismatch, not a supported integration path.

**Problem 3 — Model name format mismatch**

Vertex AI requires `@`-versioned model IDs such as:

```
claude-sonnet-4-5@20250929
claude-haiku-4-5@20251001
```

The short names used in Anthropic API mode (`claude-sonnet-4-6`, `claude-opus-4-6`) are not valid Vertex model identifiers and will be rejected at the endpoint level, independent of the proxy.

---

## Configuration B — Anthropic API Mode (works)

```
ANTHROPIC_AUTH_TOKEN=<virtual-key>
ANTHROPIC_BASE_URL=http://<proxy-host>:4000
```

### Why it works

| Step | What happens |
|---|---|
| Model name validation | None client-side — whatever model name is configured is sent directly to the server as-is. |
| URL pattern | Uses the standard Anthropic API path: `POST /v1/messages` — natively handled by LiteLLM. |
| Auth | `ANTHROPIC_AUTH_TOKEN` is sent as the `x-api-key` header, which LiteLLM's virtual key auth middleware reads and validates correctly. |
| Routing | LiteLLM matches the model name to a `model_list` entry → forwards to the backend (e.g. a `vertex_adapter` on a local port) → reaches the model farm. |

There are no startup model availability probes in Anthropic API mode, no GCP credential requirements, and no URL format constraints — making it inherently compatible with any Anthropic-compatible proxy.

---

## Summary

| Factor | Vertex Mode | Anthropic Mode |
|---|---|---|
| Model availability check | Runtime probe against GCP endpoint — fails with stub project/region | None — model name passed through to server |
| Model name format | Requires `@`-versioned Vertex IDs (e.g. `claude-sonnet-4-5@20250929`) | Accepts any string (e.g. `claude-sonnet-4-6`) |
| Request URL | `/v1/projects/.../models/{model}:rawPredict` — not a supported LiteLLM inbound path | `/v1/messages` — native LiteLLM route |
| Auth mechanism | GCP-style credentials required (partially worked around via undocumented env var) | `x-api-key` header — standard LiteLLM virtual key |
| Works with LiteLLM gateway | ❌ | ✅ |

**Bottom line:** Vertex mode is designed for connecting directly to Google Cloud Platform. It performs GCP-specific startup checks, requires properly formatted Vertex model IDs, and sends requests on a Vertex-specific URL path — none of which align with how a LiteLLM proxy operates. Anthropic API mode is provider-agnostic: it has no client-side model checks, uses the standard `/v1/messages` path, and authenticates via a simple API key header, making it the correct integration point for any Anthropic-compatible proxy or LLM gateway.
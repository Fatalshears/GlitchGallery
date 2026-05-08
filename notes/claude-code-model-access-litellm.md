# Why Claude Code + LiteLLM Gateway: Vertex Mode Fails, Anthropic Mode Works

## Setup Context

A LiteLLM proxy runs on the intranet, acting as a gateway that routes AI API calls to a backend model farm. Claude Code on a client machine connects to it over LAN.

---

## Configuration A — Vertex Mode (does NOT work)

```sh
ANTHROPIC_API_KEY=<virtual-key>
ANTHROPIC_VERTEX_BASE_URL=http://<proxy-host>:4000
CLAUDE_CODE_USE_VERTEX=1
CLOUD_ML_REGION=_
ANTHROPIC_VERTEX_PROJECT_ID=_
CLAUDE_CODE_SKIP_VERTEX_AUTH=1
```

### Why it fails

#### Problem 1 — Client-side model registry validation (root cause)

When `CLAUDE_CODE_USE_VERTEX=1` is set, Claude Code switches into Vertex AI mode. In this mode it maintains a **hardcoded internal list** of valid Vertex model identifiers (e.g. `claude-sonnet-4-5@20250929`). Before making any network call, it validates the configured model name against that list.

- The 4.6-series models (`claude-sonnet-4-6`, `claude-opus-4-6`) were released **after** Claude Code 2.1.132 was built, so they are absent from that internal list.
- Validation fails instantly on the client — `✻ Brewed for 0s` means **zero network time**; the error never reaches the proxy.
- The error `The model claude-sonnet-4-6 is not available on your vertex deployment` is generated entirely client-side.

#### Problem 2 — Vertex URL path mismatch

Even for models that pass the client-side check, Vertex mode sends requests using the Vertex AI URL pattern:

```
POST /v1/projects/{project}/locations/{region}/publishers/anthropic/models/{model}:rawPredict
```

LiteLLM has no native handler for this path. The proxy in this setup registered a custom handler in `proxy_app.py` for it, but the route only works correctly when LiteLLM's auth middleware can validate the virtual key — and the Vertex SDK sends auth differently than LiteLLM expects.

#### Problem 3 — Placeholder region/project values

Vertex mode requires real GCP `project_id` and `region` values for its auth flow. Using `_` as placeholders satisfies `CLAUDE_CODE_SKIP_VERTEX_AUTH=1` for auth skipping, but the SDK still enforces structural validation on the URL segments in some code paths.

---

## Configuration B — Anthropic API Mode (works)

```sh
ANTHROPIC_AUTH_TOKEN=<virtual-key>
ANTHROPIC_BASE_URL=http://<proxy-host>:4000
```

### Why it works

| Step | What happens |
|---|---|
| Model validation | **None** — Anthropic mode has no client-side model list check. Whatever model name is configured is sent directly to the server. |
| URL pattern | Uses the standard Anthropic API path: `POST /v1/messages` — which LiteLLM handles natively. |
| Auth | `ANTHROPIC_AUTH_TOKEN` is sent as `x-api-key` header, which LiteLLM's virtual key auth middleware reads and validates correctly. |
| Routing | LiteLLM matches the model name to a `model_list` entry → forwards to `vertex_adapter` on port 4001 → reaches the backend model farm. |

---

## Summary

| Factor | Vertex Mode | Anthropic Mode |
|---|---|---|
| Model name validation | Client-side, hardcoded list → blocks 4.6 series | None — passes model name through |
| Request URL | `/v1/projects/.../models/{model}:rawPredict` — needs custom proxy route | `/v1/messages` — native LiteLLM route |
| Auth mechanism | GCP-style, partially skipped via env var | `x-api-key` header — standard LiteLLM virtual key |
| Works with LiteLLM gateway | ❌ | ✅ |

**Bottom line:** Vertex mode is designed for connecting directly to Google Cloud Platform. It has client-side assumptions (GCP auth, known model list) that break when a LiteLLM proxy is substituted as the backend. Anthropic API mode is provider-agnostic and works correctly with any OpenAI/Anthropic-compatible proxy.
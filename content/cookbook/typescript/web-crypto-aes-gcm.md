---
title: Web Crypto AES-GCM in TypeScript
type: cookbook
tags: [cookbook, typescript, security, cryptography]
aliases: [SubtleCrypto, crypto.subtle, AES-GCM javascript, encrypt in browser]
versions: "Modern browsers (secure contexts), Node.js 20+ (globalThis.crypto)"
status: draft
levels: [2]
---

Concepts: [[end-to-end-encryption]] · [[encrypted-sharing-links]] · [[cryptographic-hash-functions]].

## API map

| Need | API |
|---|---|
| Random bytes (IV, ids) | `crypto.getRandomValues(new Uint8Array(12))` |
| New key | `crypto.subtle.generateKey({ name: "AES-GCM", length: 128 }, true, ["encrypt", "decrypt"])` |
| Key → text | `crypto.subtle.exportKey("jwk", key)` → `jwk.k` (base64url) |
| Text → key | `crypto.subtle.importKey("jwk", { kty: "oct", k, alg: "A128GCM", ext: true }, "AES-GCM", false, usages)` |
| Encrypt / decrypt | `crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, bytes)` / `decrypt(…)` |
| Text ↔ bytes | `new TextEncoder().encode(s)`, `new TextDecoder().decode(buf)` |
| Hash | `crypto.subtle.digest("SHA-256", bytes)` |
| Password → key | `importKey("raw", pwBytes, "PBKDF2", …)` + `deriveKey({ name: "PBKDF2", salt, iterations, hash: "SHA-256" }, …)` |

Everything is promise-based and works only in **secure contexts** (HTTPS or localhost).

## Recipes

> [!tested] Encrypt JSON for upload — `examples/whiteboard/typescript/src/crypto.ts`
> - **Used for:** The complete encrypt/decrypt round trip with a key you can put in a URL fragment.
> - **Input:** Any JSON-serializable value.
> - **Expected output:** `iv` (12 bytes) + `data` (ciphertext, plaintext length + 16-byte tag); `decryptJSON` returns the original value; wrong key or modified bytes reject with `OperationError`.
>
> ```ts
> import { generateKey, exportKey, importKey, encryptJSON, decryptJSON } from "./src/crypto.ts";
> const key = await generateKey();
> const { iv, data } = await encryptJSON(key, { elements: [] });
> const restored = await decryptJSON(await importKey(await exportKey(key)), iv, data);
> ```
> Run the tests: `cd examples/whiteboard/typescript && node --test`.

> [!mwe] Pack IV and ciphertext into one buffer
> - **Used for:** Sending a single binary message over WebSocket or storing one blob.
> - **Input:** `iv` and `data` from `encryptJSON`.
> - **Expected output:** One `Uint8Array` of length `12 + data.length`; `unpack` returns the two parts unchanged.
>
> ```ts
> export const pack = (iv: Uint8Array, data: Uint8Array) => {
>   const out = new Uint8Array(iv.length + data.length);
>   out.set(iv); out.set(data, iv.length);
>   return out;
> };
> export const unpack = (buf: Uint8Array) => ({ iv: buf.slice(0, 12), data: buf.slice(12) });
> ```

> [!mwe] Base64url helpers for URLs
> - **Used for:** Turning bytes into URL-safe text and back (ids, salts).
> - **Input:** A `Uint8Array`, or a base64url string.
> - **Expected output:** A string using only `A–Z a–z 0–9 - _` with no `=` padding; decoding returns the original bytes.
>
> ```ts
> export const toB64url = (b: Uint8Array) =>
>   btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
> export const fromB64url = (s: string) =>
>   Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
> ```

## Gotchas

- `crypto.subtle` is `undefined` on plain `http://` pages (except localhost).
- Never reuse an IV with the same key; always generate a fresh one per `encrypt`.
- Mark keys non-extractable (`extractable: false`) when you never need to export them.
- `String.fromCharCode(...bytes)` overflows the call stack for multi-megabyte buffers — chunk it, or use `Uint8Array.prototype.toBase64` where available.
- Errors are deliberately vague (`OperationError`) — you cannot tell "wrong key" from "tampered data", by design.

## References

- MDN, *SubtleCrypto* — https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto
- MDN, *Secure contexts* — https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts
- W3C, *Web Cryptography API* — https://www.w3.org/TR/WebCryptoAPI/

// End-to-end encryption of scenes with AES-GCM (Web Crypto: browsers and Node 22+).
//
// The key never goes to the server: share links carry it in the URL *fragment*
// (after '#'), which browsers do not send in HTTP requests.
//   https://example.app/#json=<scene-id>,<key>

const subtle = globalThis.crypto.subtle;

export async function generateKey(): Promise<CryptoKey> {
  return subtle.generateKey({ name: "AES-GCM", length: 128 }, true, ["encrypt", "decrypt"]);
}

export async function exportKey(key: CryptoKey): Promise<string> {
  const jwk = await subtle.exportKey("jwk", key);
  return jwk.k!; // base64url, safe inside a URL fragment
}

export async function importKey(k: string): Promise<CryptoKey> {
  return subtle.importKey("jwk", { kty: "oct", k, alg: "A128GCM", ext: true }, { name: "AES-GCM" }, false, [
    "encrypt",
    "decrypt",
  ]);
}

/** Encrypt any JSON value. A fresh 12-byte IV per message is required for AES-GCM security. */
export async function encryptJSON(key: CryptoKey, value: unknown) {  // return type inferred: Uint8Array<ArrayBuffer> on TS >= 5.7
  const iv = globalThis.crypto.getRandomValues(new Uint8Array(12));
  const plain = new TextEncoder().encode(JSON.stringify(value));
  return { iv, data: new Uint8Array(await subtle.encrypt({ name: "AES-GCM", iv }, key, plain)) };
}

/** Throws (OperationError) if the key is wrong or the ciphertext was tampered with. */
export async function decryptJSON<T>(key: CryptoKey, iv: BufferSource, data: BufferSource): Promise<T> {
  const plain = await subtle.decrypt({ name: "AES-GCM", iv }, key, data);
  return JSON.parse(new TextDecoder().decode(plain)) as T;
}

/** Split "#json=<id>,<key>" into its parts; null if the fragment is not a share link. */
export function parseShareFragment(hash: string): { id: string; key: string } | null {
  const m = /^#json=([A-Za-z0-9_-]+),([A-Za-z0-9_-]+)$/.exec(hash);
  return m ? { id: m[1], key: m[2] } : null;
}

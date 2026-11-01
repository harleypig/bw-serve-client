// Register BW_EMAIL / BW_PASSWORD on the Vaultwarden at VW_URL.
//
// The bw CLI has no register command, and a Bitwarden server stores only
// what the client derives, so this does the client's half:
//
//   master key   PBKDF2-SHA256(password, salt = email, KDF_ITERATIONS)
//   auth hash    PBKDF2-SHA256(master key, salt = password, 1)
//   stretched    HKDF-Expand(master key, "enc" | "mac"), 32 bytes each
//   user key     64 random bytes, wrapped by the stretched key
//   key pair     RSA-2048; the private half wrapped by the user key
//
// Each wrap is a type-2 EncString: AES-256-CBC, then HMAC-SHA256 over
// iv || ciphertext, written "2.<iv>|<ct>|<mac>" in base64.
//
// Vaultwarden 1.37 registers in two calls: send-verification-email returns
// a token when no mail is configured, and register/finish takes it.

"use strict";

const crypto = require("node:crypto");

const KDF_ITERATIONS = 600000;

// Vaultwarden takes a few seconds to open its port; 60 one-second tries
// covers a cold start on a slow machine without hanging a broken one.
const READY_TRIES = 60;

const { VW_URL, BW_EMAIL, BW_PASSWORD } = process.env;

// HKDF-Expand alone: Bitwarden treats the master key as the PRK and skips
// the extract step, which node's hkdfSync always performs.
function hkdfExpand(prk, info, length) {
  let block = Buffer.alloc(0);
  let out = Buffer.alloc(0);

  for (let i = 1; out.length < length; i++) {
    block = crypto.createHmac("sha256", prk).update(Buffer.concat([block, Buffer.from(info), Buffer.from([i])])).digest();
    out = Buffer.concat([out, block]);
  }

  return out.subarray(0, length);
}

function encString(plain, encKey, macKey) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv("aes-256-cbc", encKey, iv);
  const ct = Buffer.concat([cipher.update(plain), cipher.final()]);
  const mac = crypto.createHmac("sha256", macKey).update(Buffer.concat([iv, ct])).digest();

  return `2.${iv.toString("base64")}|${ct.toString("base64")}|${mac.toString("base64")}`;
}

async function waitForServer() {
  for (let i = 0; i < READY_TRIES; i++) {
    try {
      const res = await fetch(`${VW_URL}/alive`);

      if (res.ok) return;
    } catch {
      // Not listening yet.
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  throw new Error(`Vaultwarden at ${VW_URL} did not come up`);
}

async function post(path, body) {
  const res = await fetch(`${VW_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });

  // The response body is the server's error text; it holds no secret.
  if (!res.ok) throw new Error(`${path}: ${res.status} ${await res.text()}`);

  return res.status === 204 ? null : res.json();
}

async function main() {
  const email = BW_EMAIL.trim().toLowerCase();
  const masterKey = crypto.pbkdf2Sync(BW_PASSWORD, email, KDF_ITERATIONS, 32, "sha256");
  const authHash = crypto.pbkdf2Sync(masterKey, BW_PASSWORD, 1, 32, "sha256").toString("base64");
  const userKey = crypto.randomBytes(64);

  const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", {
    modulusLength: 2048,
    publicKeyEncoding: { type: "spki", format: "der" },
    privateKeyEncoding: { type: "pkcs8", format: "der" },
  });

  await waitForServer();

  const token = await post("/identity/accounts/register/send-verification-email", { email, name: "Fixture Recorder" });

  await post("/identity/accounts/register/finish", {
    email,
    emailVerificationToken: token,
    masterPasswordHash: authHash,
    masterPasswordHint: null,
    kdf: 0,
    kdfIterations: KDF_ITERATIONS,
    key: encString(userKey, hkdfExpand(masterKey, "enc", 32), hkdfExpand(masterKey, "mac", 32)),
    keys: {
      publicKey: publicKey.toString("base64"),
      encryptedPrivateKey: encString(privateKey, userKey.subarray(0, 32), userKey.subarray(32)),
    },
  });
}

main().catch((err) => {
  console.error(`register.js: ${err.message}`);
  process.exit(1);
});

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
//
// bw serve cannot create an organization, so this also logs in over the
// API and creates one, the way the web vault would, for the organization
// and collection routes to have something to answer about:
//
//   org key      64 random bytes, wrapped for the account by RSA-OAEP-SHA1
//                with the account's public key (a type-4 EncString)
//   org pair     RSA-2048; the private half wrapped by the org key
//   collection   its name a type-2 EncString under the org key; Vaultwarden
//                creates it with the organization, the account as owner

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

async function post(path, body, token) {
  const headers = { "Content-Type": "application/json", Accept: "application/json" };

  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${VW_URL}${path}`, { method: "POST", headers, body: JSON.stringify(body) });

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

  await createOrganization(email, authHash, publicKey);
}

// Log in with the password grant and return the access token. The token
// lives only in this process; the device fields are what Vaultwarden
// requires of any login, and name a device that exists for this run.
async function accessToken(email, authHash) {
  const form = new URLSearchParams({
    grant_type: "password",
    username: email,
    password: authHash,
    scope: "api offline_access",
    client_id: "web",
    deviceIdentifier: crypto.randomUUID(),
    deviceName: "fixture-recorder",
    deviceType: "9",
  });

  const res = await fetch(`${VW_URL}/identity/connect/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
    body: form,
  });

  // As in post(): the body of a refusal is the server's error text.
  if (!res.ok) throw new Error(`/identity/connect/token: ${res.status} ${await res.text()}`);

  return (await res.json()).access_token;
}

async function createOrganization(email, authHash, userPublicKey) {
  const token = await accessToken(email, authHash);
  const orgKey = crypto.randomBytes(64);
  const encKey = orgKey.subarray(0, 32);
  const macKey = orgKey.subarray(32);

  const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", {
    modulusLength: 2048,
    publicKeyEncoding: { type: "spki", format: "der" },
    privateKeyEncoding: { type: "pkcs8", format: "der" },
  });

  const wrapped = crypto.publicEncrypt(
    {
      key: crypto.createPublicKey({ key: userPublicKey, format: "der", type: "spki" }),
      padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
      oaepHash: "sha1",
    },
    orgKey,
  );

  await post(
    "/api/organizations",
    {
      name: "Recorded organization",
      billingEmail: email,
      planType: 0,
      key: `4.${wrapped.toString("base64")}`,
      collectionName: encString(Buffer.from("Recorded collection"), encKey, macKey),
      keys: { publicKey: publicKey.toString("base64"), encryptedPrivateKey: encString(privateKey, encKey, macKey) },
    },
    token,
  );
}

main().catch((err) => {
  console.error(`register.js: ${err.message}`);
  process.exit(1);
});

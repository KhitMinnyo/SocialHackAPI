# Lab: API Gateway Misconfiguration — Path & Trust Bypass

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Bypass a simulated API Gateway's protection using three independent techniques |
| **Difficulty** | ⭐⭐ Medium                                           |
| **Time**       | 35 minutes                                            |
| **Category**   | Gateway / Path Normalization                             |
| **OWASP**      | API8:2023 - Security Misconfiguration                    |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- `curl` or Python 3 with the `requests` library
- Read the caveat in Tutorial 7.7 first — this lab simulates gateway misconfiguration within a single Flask process; real multi-tier gateway bugs (nginx vs. backend, Kong vs. upstream) can be more complex than what's shown here

---

## Background

`GET /api/v1/gateway-internal/stats` is meant to be reachable only through a trusted API Gateway. A `before_request` hook in `app/__init__.py` (`fake_gateway_layer`) simulates that gateway's protection: it blocks the exact path string unless a trust header is present. Three independent bypass techniques exist because the "gateway" check and the actual routing/data-serving logic don't agree with each other.

---

## Tasks

### Task 1: Confirm the Endpoint Is Protected

**Steps:**
1. Request the protected path directly with no special headers

**curl example:**
```bash
curl -s -i http://localhost:5001/api/v1/gateway-internal/stats
```

**🚩 FLAG 1: What status code and error message do you get?**

---

### Task 2: Bypass via Trailing Slash

**Steps:**
1. Request the exact same logical endpoint, but with a trailing slash appended

**curl example:**
```bash
curl -s -i http://localhost:5001/api/v1/gateway-internal/stats/
```

**🚩 FLAG 2: What is the `flag` value in the JSON response now that you've bypassed the check?**

<details>
<summary>💡 Hint 1</summary>
The gateway's blocklist does an exact string comparison against `request.path` — it never strips or adds a trailing slash before comparing.
</details>

---

### Task 3: Bypass via Alias Route

**Steps:**
1. Try a differently-named path that might expose the same data

**curl example:**
```bash
curl -s -i http://localhost:5001/api/v1/internal/infra-stats
```

**🚩 FLAG 3: Confirm this returns the same data as the protected endpoint, with no bypass trick needed at all**

<details>
<summary>💡 Hint 1</summary>
Check `/openapi.json` (Stage 3.4) for hints about what's "internal" — but note this specific alias path was deliberately left OUT of that spec, so you'll need to think about what alternate route naming a team might use for the same service (`/gateway-internal/...` vs `/internal/...`).
</details>

---

### Task 4: Bypass via Spoofed Trust Header

**Steps:**
1. Discover the expected header name/value (check `/openapi.json`'s description field for this endpoint)
2. Add it yourself and hit the originally-blocked path directly

**curl example:**
```bash
curl -s -i http://localhost:5001/api/v1/gateway-internal/stats \
  -H "X-Gateway-Verified: trusted-internal-99"
```

**🚩 FLAG 4: Confirm the header alone is sufficient — no actual gateway involved**

<details>
<summary>💡 Hint 1</summary>
This is the header-trust flaw: there's nothing cryptographically binding this header to "the request really came through the gateway." It's just a string any client can set.
</details>

---

### Task 5: Which Bypass Is "Best" and Why?

**🚩 FLAG 5: Rank the three bypasses by how much prior knowledge/recon they require, from least to most**

<details>
<summary>💡 Hint 1</summary>
Think about it from an attacker's perspective: which one works with zero recon at all, which needs you to have found `/openapi.json` first, and which needs you to guess a plausible alternate route name?
</details>

---

## Flags to Find

| Flag   | Description                                                | Hint                                       |
|--------|--------------------------------------------------------------|-----------------------------------------------|
| FLAG 1 | Status code + error for the blocked direct request             | Plain GET, no headers                          |
| FLAG 2 | Flag value retrieved via trailing-slash bypass                  | Append `/` to the protected path               |
| FLAG 3 | Confirm the alias route leaks the same data                     | Try `/api/v1/internal/infra-stats`             |
| FLAG 4 | Confirm the spoofed header bypasses protection                  | Add `X-Gateway-Verified` yourself              |
| FLAG 5 | Rank the three bypasses by recon effort required                 | Think about what each technique needs to know  |

---

## Remediation

### 1. Normalize Paths Consistently on Both Sides
```python
normalized_path = request.path.rstrip("/")
if normalized_path in GATEWAY_BLOCKED_EXACT_PATHS:
    ...
```

### 2. Use an Allowlist, Not a Blocklist
```python
PUBLIC_PATHS = {"/api/v1/auth/login", "/api/v1/posts", ...}
if request.path not in PUBLIC_PATHS and not is_internal_service_call():
    return jsonify({"error": "Forbidden"}), 403
```

### 3. Use Cryptographic Binding Instead of a Plain Header
- Mutual TLS (mTLS) between gateway and backend, or signed/HMAC'd requests, so the backend can actually verify the request came through the gateway.

### 4. Network-Level Segmentation
- The backend should not be reachable from the public internet at all — only from the gateway's IP range/VPC.

### 5. Keep Gateway Rules in Sync With the Route Table
- Automate this: fail CI if a new backend route isn't reflected in the gateway's configuration.

---

## References

- [OWASP API Security Top 10 - API8:2023](https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/)
- [CWE-444: Inconsistent Interpretation of HTTP Requests](https://cwe.mitre.org/data/definitions/444.html)
- [PortSwigger: HTTP Request Smuggling](https://portswigger.net/web-security/request-smuggling)

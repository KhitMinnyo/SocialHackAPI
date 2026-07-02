# Lab: Postman Basics — Interacting with APIs

## Objective

Learn the fundamentals of interacting with RESTful APIs using curl (simulating Postman workflows). You will authenticate, retrieve data, create resources, and practice using different HTTP methods against the SocialHack API.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Easy |
| **Estimated Time** | 30 minutes |
| **Prerequisites** | curl installed, basic terminal knowledge, Python 3 with `requests` |
| **OWASP API Category** | N/A — Foundational skills |

---

## Background

### What Is Postman?

Postman is a popular API development and testing tool that provides a graphical interface for sending HTTP requests. In a security testing context, we often use **curl** on the command line to achieve the same goals — sending carefully crafted HTTP requests to discover how an API behaves.

### HTTP Methods Overview

| Method | Purpose | Idempotent? |
|---|---|---|
| **GET** | Retrieve a resource | Yes |
| **POST** | Create a new resource | No |
| **PUT** | Update (replace) a resource | Yes |
| **PATCH** | Partially update a resource | No |
| **DELETE** | Remove a resource | Yes |
| **OPTIONS** | Query supported methods | Yes |

### Anatomy of an HTTP Request

```
POST /api/v1/auth/login HTTP/1.1        ← Method + Path
Host: localhost:5001                      ← Target host
Content-Type: application/json           ← Header: body format
Authorization: Bearer <token>            ← Header: authentication

{"username":"alice","password":"pass"}   ← Request body (JSON)
```

### Common curl Flags

| Flag | Meaning | Example |
|---|---|---|
| `-X` | HTTP method | `-X POST` |
| `-H` | Add a header | `-H "Content-Type: application/json"` |
| `-d` | Request body (data) | `-d '{"key":"value"}'` |
| `-s` | Silent mode | Suppress progress bar |
| `-v` | Verbose mode | Show full request/response headers |
| `-o` | Output to file | `-o response.json` |

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5001` |
| Test User | alice / password123 |
| Auth Method | JWT Bearer Token |

---

## Tasks

### Task 1: Login and Obtain a JWT Token

**Goal:** Authenticate with the API and save the JWT token for subsequent requests.

**Steps:**

1. Send a login request as alice:

```bash
curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

2. Examine the JSON response. You should see a `token` field.

3. Save the token to a shell variable for reuse:

```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

echo $TOKEN
```

4. Try sending a request **without** a token and note the difference:

```bash
curl -s http://localhost:5001/api/v1/users/1
```

> **🚩 FLAG 1:** What is the HTTP status code returned when accessing `/api/v1/users/1` without a token?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
APIs that require authentication typically return a 4xx status code when no credentials are provided.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
The most common status code for "not authenticated" is <code>401 Unauthorized</code>. Use <code>curl -s -o /dev/null -w "%{http_code}"</code> to see just the status code.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
Run: <code>curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/users/1</code>. The answer is <code>401</code>.
</details>

---

### Task 2: Retrieve Your User Profile

**Goal:** Use the saved token to fetch alice's profile data.

**Steps:**

1. Send an authenticated GET request:

```bash
curl -s http://localhost:5001/api/v1/users/1 \
  -H "Authorization: Bearer $TOKEN"
```

2. Pipe the output through `python3 -m json.tool` for pretty-printing:

```bash
curl -s http://localhost:5001/api/v1/users/1 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

3. Note the fields returned in the user profile: `id`, `username`, `email`, `role`, etc.

4. Now use verbose mode to inspect the full HTTP exchange:

```bash
curl -v http://localhost:5001/api/v1/users/1 \
  -H "Authorization: Bearer $TOKEN" 2>&1
```

> **🚩 FLAG 2:** What is alice's email address returned by the API?

<details>
<summary>Hint 1</summary>
The response JSON will contain an <code>email</code> field. Look through the output carefully.
</details>

<details>
<summary>Hint 2</summary>
Most test APIs use a pattern like <code>username@example.com</code> for default users.
</details>

<details>
<summary>Hint 3</summary>
Alice's email is likely <code>alice@socialhack.com</code> or <code>alice@example.com</code>. Check the actual response.
</details>

---

### Task 3: Create a New Post

**Goal:** Use a POST request to create new content on the platform.

**Steps:**

1. Create a new post:

```bash
curl -s -X POST http://localhost:5001/api/v1/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"My First Post","content":"Hello from the API!"}'
```

2. Note the response — it should contain the newly created post with an `id`.

3. Retrieve the post by its ID (replace `<id>` with the returned ID):

```bash
curl -s http://localhost:5001/api/v1/posts/<id> \
  -H "Authorization: Bearer $TOKEN"
```

4. Try creating a post without a title and observe the validation error:

```bash
curl -s -X POST http://localhost:5001/api/v1/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content":"Missing title"}'
```

> **🚩 FLAG 3:** What is the `id` of the post you created?

<details>
<summary>Hint 1</summary>
The API returns the created resource in the response body. Look for the <code>id</code> field.
</details>

<details>
<summary>Hint 2</summary>
The ID will be an integer. If existing posts already exist, it might be something like 4, 5, 6, etc.
</details>

<details>
<summary>Hint 3</summary>
The exact ID depends on how many posts already exist in the database. Check the response JSON from your POST request.
</details>

---

### Task 4: List All Posts

**Goal:** Retrieve all posts using GET and understand pagination/listing.

**Steps:**

1. Get all posts:

```bash
curl -s http://localhost:5001/api/v1/posts \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

2. Count the number of posts returned.

3. Try accessing the endpoint with different methods to see what's allowed:

```bash
# OPTIONS request to see allowed methods
curl -s -X OPTIONS http://localhost:5001/api/v1/posts \
  -H "Authorization: Bearer $TOKEN" -v 2>&1 | grep -i "allow"
```

---

### Task 5: Practice Different HTTP Methods

**Goal:** Use PUT and DELETE on posts to understand the full CRUD lifecycle.

**Steps:**

1. Update your post using PUT (replace `<id>` with your post's ID):

```bash
curl -s -X PUT http://localhost:5001/api/v1/posts/<id> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Updated Title","content":"Updated content via PUT"}'
```

2. Verify the update by fetching the post again:

```bash
curl -s http://localhost:5001/api/v1/posts/<id> \
  -H "Authorization: Bearer $TOKEN"
```

3. Delete the post:

```bash
curl -s -X DELETE http://localhost:5001/api/v1/posts/<id> \
  -H "Authorization: Bearer $TOKEN"
```

4. Try fetching the deleted post — what happens?

```bash
curl -s http://localhost:5001/api/v1/posts/<id> \
  -H "Authorization: Bearer $TOKEN"
```

> **🚩 FLAG 4:** What HTTP status code is returned when trying to access a deleted post?

<details>
<summary>Hint 1</summary>
When a resource doesn't exist, the API should return a "not found" error.
</details>

<details>
<summary>Hint 2</summary>
The standard HTTP status code for "resource not found" is <code>404</code>.
</details>

<details>
<summary>Hint 3</summary>
Run: <code>curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/posts/&lt;id&gt; -H "Authorization: Bearer $TOKEN"</code>. The answer is <code>404</code>.
</details>

---

## Flags Summary

| Flag | Description | Expected Value |
|---|---|---|
| FLAG 1 | Status code without authentication | `401` |
| FLAG 2 | Alice's email address | Check API response |
| FLAG 3 | ID of the created post | Varies (integer) |
| FLAG 4 | Status code for deleted resource | `404` |

---

## Remediation

This lab does not exploit vulnerabilities — it teaches foundational API interaction skills. However, here are best practices for API developers:

### 1. Always Require Authentication

```python
@app.before_request
def require_auth():
    if request.endpoint not in PUBLIC_ENDPOINTS:
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Authentication required"}), 401
```

### 2. Return Proper HTTP Status Codes

| Code | Meaning | When to Use |
|---|---|---|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid auth |
| 404 | Not Found | Resource doesn't exist |

### 3. Validate Request Bodies

```python
from marshmallow import Schema, fields, validate

class PostSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    content = fields.String(required=True, validate=validate.Length(min=1, max=5000))
```

---

## References

- [curl Documentation](https://curl.se/docs/manual.html)
- [Postman Learning Center](https://learning.postman.com/)
- [HTTP Methods — MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
- [REST API Best Practices](https://restfulapi.net/)
- [JWT.io — JWT Debugger](https://jwt.io/)

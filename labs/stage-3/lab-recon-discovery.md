# Lab: Reconnaissance & API Discovery

## Objective

Perform systematic reconnaissance on the SocialHack API to enumerate all available endpoints, discover hidden functionality, identify supported HTTP methods, and map the complete API attack surface before exploitation.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Easy-Medium |
| **Estimated Time** | 45 minutes |
| **Prerequisites** | Labs 01–02 completed, curl, Python 3 with `requests` |
| **OWASP API Category** | API9:2023 – Improper Inventory Management |

---

## Background

### Why API Reconnaissance Matters

Before exploiting any API, an attacker must **discover** what endpoints exist, what methods they accept, and what data they return. This is the "information gathering" phase and is analogous to port scanning in network pentesting.

### Common API Discovery Techniques

| Technique | Description |
|---|---|
| **Path brute-forcing** | Try common API paths like `/api/v1/users`, `/api/v1/admin`, `/api/v1/debug` |
| **Method enumeration** | Test each endpoint with GET, POST, PUT, DELETE, OPTIONS, PATCH |
| **Version fuzzing** | Try `/api/v1/`, `/api/v2/`, `/api/v3/` |
| **Documentation endpoints** | Check for `/docs`, `/swagger`, `/openapi.json`, `/graphql` |
| **Error message analysis** | Different error codes reveal whether an endpoint exists |
| **OPTIONS requests** | May reveal allowed methods via `Allow` header |

### HTTP Status Code Indicators

| Code | Meaning for Recon |
|---|---|
| **200** | Endpoint exists and is accessible |
| **401** | Endpoint exists, requires authentication |
| **403** | Endpoint exists, not authorized |
| **404** | Endpoint does NOT exist |
| **405** | Endpoint exists, but method not allowed |

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5001` |
| Auth Required | Some endpoints require JWT |
| Known User | alice / password123 |

---

## Tasks

### Task 1: Enumerate API Base Paths

**Goal:** Discover all top-level API resource paths by testing common names.

**Steps:**

1. First, get an authentication token:

```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

2. Test a list of common API paths. For each, note the status code:

```bash
PATHS=(
  "/api/v1/users"
  "/api/v1/posts"
  "/api/v1/comments"
  "/api/v1/messages"
  "/api/v1/admin"
  "/api/v1/admin/users"
  "/api/v1/admin/stats"
  "/api/v1/auth"
  "/api/v1/upload"
  "/api/v1/export"
  "/api/v1/export/profile"
  "/api/v1/debug"
  "/api/v1/graphql"
  "/api/v1/tools"
  "/api/v1/tools/ping"
  "/api/v1/tools/dns-lookup"
  "/api/v1/tools/user-lookup"
  "/api/v1/webhook"
  "/api/v1/webhook/list"
  "/api/v1/webhook/register"
  "/api/v1/docs"
  "/api/v1/swagger"
  "/api/v1/openapi.json"
  "/api/v1/health"
  "/api/v1/status"
  "/api/v2/users"
)

for path in "${PATHS[@]}"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5001${path}" \
    -H "Authorization: Bearer $TOKEN")
  echo "$STATUS  $path"
done
```

3. Record which paths return 200, 401, 403, or 405 (these exist) vs. 404 (don't exist).

> **🚩 FLAG 1:** How many unique endpoint paths return a non-404 status code?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
Any status code other than 404 indicates the endpoint exists. Count all paths that return 200, 401, 403, or 405.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
The API has endpoints under: <code>/auth</code>, <code>/users</code>, <code>/posts</code>, <code>/messages</code>, <code>/admin</code>, <code>/upload</code>, <code>/export</code>, <code>/tools</code>, <code>/webhook</code>, and <code>/graphql</code>. Some paths like <code>/docs</code> and <code>/swagger</code> may return 404.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
You should find approximately 15-20 valid endpoint paths. The exact count depends on whether the API also has <code>/debug</code> and <code>/health</code> endpoints. Tools endpoints include <code>/ping</code>, <code>/dns-lookup</code>, and <code>/user-lookup</code>.
</details>

---

### Task 2: Enumerate HTTP Methods per Endpoint

**Goal:** For each discovered endpoint, determine which HTTP methods are accepted.

**Steps:**

1. Test common methods against key endpoints:

```bash
ENDPOINTS=(
  "/api/v1/users/1"
  "/api/v1/posts"
  "/api/v1/posts/1"
  "/api/v1/admin/users"
  "/api/v1/graphql"
  "/api/v1/tools/ping"
  "/api/v1/webhook/register"
)

METHODS=("GET" "POST" "PUT" "DELETE" "OPTIONS" "PATCH")

for endpoint in "${ENDPOINTS[@]}"; do
  echo ""
  echo "=== $endpoint ==="
  for method in "${METHODS[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
      "http://localhost:5001${endpoint}" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json")
    if [ "$STATUS" != "404" ] && [ "$STATUS" != "405" ]; then
      echo "  $method → $STATUS ✓"
    else
      echo "  $method → $STATUS"
    fi
  done
done
```

2. Pay special attention to endpoints that accept unexpected methods (e.g., DELETE on user resources, POST on admin endpoints).

3. Test OPTIONS to see if the API reveals allowed methods:

```bash
curl -s -X OPTIONS http://localhost:5001/api/v1/posts \
  -H "Authorization: Bearer $TOKEN" -v 2>&1 | grep -i "allow\|access-control"
```

<details>
<summary>Hint 1</summary>
Endpoints like <code>/api/v1/posts</code> typically accept GET (list) and POST (create). Individual resources like <code>/api/v1/posts/1</code> accept GET, PUT, and DELETE.
</details>

<details>
<summary>Hint 2</summary>
The <code>/api/v1/graphql</code> endpoint should accept both GET and POST. Tools endpoints like <code>/ping</code> typically only accept POST.
</details>

<details>
<summary>Hint 3</summary>
Build a table: <code>/api/v1/posts</code> → GET, POST; <code>/api/v1/posts/1</code> → GET, PUT, DELETE; <code>/api/v1/graphql</code> → GET, POST; <code>/api/v1/tools/ping</code> → POST; etc.
</details>

---

### Task 3: Discover the GraphQL Endpoint

**Goal:** Find and verify the GraphQL endpoint, then confirm introspection is enabled.

**Steps:**

1. Test the GraphQL endpoint with a simple query:

```bash
# GET request with query parameter
curl -s "http://localhost:5001/api/v1/graphql?query=\{__typename\}" \
  -H "Authorization: Bearer $TOKEN"
```

2. Try a POST request with a JSON body:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __typename }"}'
```

3. Check if introspection is enabled (this is a major security finding):

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __schema { queryType { name } } }"}' | python3 -m json.tool
```

> **🚩 FLAG 2:** What is the full GraphQL endpoint URL?

<details>
<summary>Hint 1</summary>
GraphQL endpoints are commonly found at <code>/graphql</code>, <code>/api/graphql</code>, or <code>/api/v1/graphql</code>.
</details>

<details>
<summary>Hint 2</summary>
Try sending a POST request with <code>{"query":"{ __typename }"}</code> to <code>/api/v1/graphql</code>. If it responds with data, you found it.
</details>

<details>
<summary>Hint 3</summary>
The GraphQL endpoint is <code>http://localhost:5001/api/v1/graphql</code>. It accepts both GET and POST requests.
</details>

---

### Task 4: Discover Tool Endpoints

**Goal:** Find all available tool/utility endpoints and understand what they do.

**Steps:**

1. Test each tools endpoint:

```bash
# Test ping tool
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1"}'

# Test dns-lookup tool
curl -s -X POST http://localhost:5001/api/v1/tools/dns-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain":"example.com"}'

# Test user-lookup tool
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":"alice"}'
```

2. For each tool, note:
   - What parameters it accepts
   - What data it returns
   - Whether it processes input in a potentially dangerous way

3. Try sending malformed input to see error messages:

```bash
# Empty body
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{}'

# Invalid parameter
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":""}'
```

> **🚩 FLAG 3:** What tool endpoints exist? List them all.

<details>
<summary>Hint 1</summary>
There are three tool endpoints under <code>/api/v1/tools/</code>. You can find them by testing common names or fuzzing.
</details>

<details>
<summary>Hint 2</summary>
The tools are network/system utilities: one for ICMP, one for DNS, and one for user lookups.
</details>

<details>
<summary>Hint 3</summary>
The three tool endpoints are: <code>/api/v1/tools/ping</code>, <code>/api/v1/tools/dns-lookup</code>, and <code>/api/v1/tools/user-lookup</code>.
</details>

---

### Task 5: Map the Complete API Surface

**Goal:** Create a comprehensive map of all endpoints, methods, authentication requirements, and potential attack vectors.

**Steps:**

1. Compile your findings into a structured table. Test each endpoint both with and without authentication:

```bash
# Test without auth
for path in "/api/v1/users/1" "/api/v1/posts" "/api/v1/admin/users" "/api/v1/graphql" "/api/v1/tools/ping" "/api/v1/webhook/list"; do
  STATUS_NO_AUTH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5001${path}")
  STATUS_AUTH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5001${path}" \
    -H "Authorization: Bearer $TOKEN")
  echo "$path → NoAuth:$STATUS_NO_AUTH  Auth:$STATUS_AUTH"
done
```

2. Test the webhook endpoints:

```bash
# List webhooks
curl -s http://localhost:5001/api/v1/webhook/list \
  -H "Authorization: Bearer $TOKEN"

# Register a webhook
curl -s -X POST http://localhost:5001/api/v1/webhook/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url":"http://example.com/hook","event":"user.created"}'
```

3. Create your API map using this template:

| Endpoint | Methods | Auth Required | Notes |
|---|---|---|---|
| `/api/v1/auth/login` | POST | No | Returns JWT |
| `/api/v1/auth/register` | POST | No | Creates user |
| `/api/v1/users/:id` | GET, PUT, DELETE | Yes | User profiles |
| `/api/v1/posts` | GET, POST | Yes | Post management |
| `/api/v1/admin/users` | GET | Yes | Admin panel |
| `/api/v1/graphql` | GET, POST | Varies | GraphQL API |
| `/api/v1/tools/ping` | POST | Yes | Network tool |
| `/api/v1/tools/dns-lookup` | POST | Yes | DNS tool |
| `/api/v1/tools/user-lookup` | POST | Yes | User search |
| `/api/v1/webhook/register` | POST | Yes | Webhook mgmt |
| `/api/v1/webhook/list` | GET | Yes | List webhooks |
| `/api/v1/webhook/test/:id` | POST | Yes | Test webhook |

<details>
<summary>Hint 1</summary>
A complete API map should include at least 15-20 unique endpoint patterns. Don't forget to check for sub-resources like <code>/posts/:id/comments</code> and <code>/posts/:id/like</code>.
</details>

<details>
<summary>Hint 2</summary>
Test version-prefixed paths: <code>/api/v2/</code> may exist. Also check for documentation endpoints like <code>/api/v1/docs</code>.
</details>

<details>
<summary>Hint 3</summary>
The complete API surface includes: auth (login, register, reset-password, refresh), users (CRUD, search, followers), posts (CRUD, like, comments), messages (read, send, conversations), admin (users, stats), upload (avatar), export (profile), tools (ping, dns-lookup, user-lookup), webhook (register, test, list), and graphql.
</details>

---

## Flags Summary

| Flag | Description | Expected Value |
|---|---|---|
| FLAG 1 | Number of unique endpoint paths returning non-404 | ~15-20 |
| FLAG 2 | Full GraphQL endpoint URL | `http://localhost:5001/api/v1/graphql` |
| FLAG 3 | Tool endpoints that exist | `/tools/ping`, `/tools/dns-lookup`, `/tools/user-lookup` |

---

## Remediation

### 1. Disable Unnecessary Endpoints in Production

```python
if app.config["ENV"] == "production":
    # Remove debug, tools, and test endpoints
    app.register_blueprint(tools_bp)  # ← Don't do this in prod
```

### 2. Disable GraphQL Introspection

```python
from graphql import GraphQLSchema

schema = GraphQLSchema(
    query=QueryType,
    mutation=MutationType,
    # Disable introspection in production
    directives=[]
)

# Or use a middleware
class DisableIntrospection:
    def resolve(self, next, root, info, **args):
        if info.field_name in ("__schema", "__type"):
            raise Exception("Introspection is disabled")
        return next(root, info, **args)
```

### 3. Implement Proper API Versioning

```python
# Only expose current version
app.register_blueprint(api_v1, url_prefix="/api/v1")
# Remove old versions in production
# app.register_blueprint(api_v2, url_prefix="/api/v2")  # deprecated
```

### 4. Use an API Gateway

An API gateway can:
- Rate limit by endpoint
- Block access to internal/admin endpoints from external traffic
- Log all API requests for monitoring
- Enforce authentication policies centrally

### 5. Return Consistent Error Codes

```python
# Don't reveal whether an endpoint exists
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Not found"}), 404  # Same as 404 to prevent enumeration
```

---

## References

- [OWASP API9:2023 — Improper Inventory Management](https://owasp.org/API-Security/editions/2023/en/0xa9-improper-inventory-management/)
- [OWASP API Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [GraphQL Security — Introspection](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [API Discovery Best Practices](https://portswigger.net/web-security/api-testing)
- [Kiterunner — API Discovery Tool](https://github.com/assetnote/kiterunner)

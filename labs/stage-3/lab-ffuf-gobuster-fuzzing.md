# Lab: ffuf & gobuster — Directory/Endpoint Fuzzing

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Discover hidden, undocumented endpoints via wordlist fuzzing |
| **Difficulty** | ⭐ Easy                                              |
| **Time**       | 30 minutes                                            |
| **Category**   | Reconnaissance / Tooling                               |
| **OWASP**      | API9:2023 - Improper Inventory Management               |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- `ffuf` and/or `gobuster` installed (see Tutorial 3.5 for install instructions)
- If neither tool is available, use the Python fallback fuzzer in the solution script — the lab works either way
- `jq` recommended for reading JSON responses

---

## Background

SocialHack API's `/api/v1/debug` endpoint normally dumps every registered Flask route — a huge recon shortcut used in earlier labs. This time, a handful of endpoints have been deliberately filtered out of that dump. They're still completely live and unauthenticated; they're just no longer listed anywhere. The only realistic way to find them is the same way a real attacker would: wordlist-based directory/file fuzzing.

---

## Tasks

### Task 1: Confirm the Debug Dump Doesn't Help This Time

**Steps:**
1. Query the debug endpoint and search for anything related to backups, `.env`, or old admin panels

**Python example:**
```python
import requests

r = requests.get("http://localhost:5001/api/v1/debug")
routes = r.json()["registered_routes"]
suspicious = [x for x in routes if any(k in x.lower() for k in ("backup", "env", "admin_old", "old"))]
print(f"Suspicious routes found via debug dump: {suspicious}")
```

<details>
<summary>💡 Hint 1</summary>
This should print an empty list — that's the point. The debug dump has been filtered.
</details>

---

### Task 2: Build a Wordlist and Fuzz the Root

**Steps:**
1. Create a small custom wordlist (or use a real one like SecLists' `raft-small-directories.txt`)
2. Run `ffuf` or `gobuster` against the API root

**ffuf example:**
```bash
cat > wordlist.txt <<EOF
backup
.env
admin_old
old
staging
internal
private
config
test
dev
EOF

ffuf -u http://localhost:5001/FUZZ -w wordlist.txt -mc 200,201,401,403 -fc 404
```

**gobuster example:**
```bash
gobuster dir -u http://localhost:5001 -w wordlist.txt -s 200,201,401,403
```

**🚩 FLAG 1: Which three words from your wordlist return HTTP 200?**

<details>
<summary>💡 Hint 1</summary>
Try including common backup/staging-related words: "backup", ".env", "admin_old".
</details>

---

### Task 3: Fuzz Recursively Inside `/backup`

**Steps:**
1. Once `/backup` returns 200, fuzz *inside* it for a specific filename

**ffuf example:**
```bash
cat > files.txt <<EOF
socialhack_db_2024
old_config
README
EOF

ffuf -u http://localhost:5001/backup/FUZZ -w files.txt -e .sql.bak,.json.bak,.txt -mc 200 -fc 404
```

**🚩 FLAG 2: What is the full filename of the discovered backup file, and what flag string is embedded in its contents?**

<details>
<summary>💡 Hint 1</summary>
The `/backup` directory listing response itself gives you a strong hint about the exact filename — check it before fuzzing blind.
</details>

---

### Task 4: Retrieve the Leaked `.env` File

**Steps:**
1. Fetch `/.env` directly and note which secrets it leaks

**curl example:**
```bash
curl -s http://localhost:5001/.env
```

**🚩 FLAG 3: Does the leaked JWT_SECRET_KEY match the one from the `/api/v1/debug` endpoint in earlier labs?**

<details>
<summary>💡 Hint 1</summary>
Compare against what you retrieved in Lab 06 (BFLA) — if they match, this is a second independent path to the same critical secret.
</details>

---

### Task 5: Find the Old Admin Panel

**Steps:**
1. Fetch `/admin_old` and read the response carefully

**🚩 FLAG 4: What does the hint in the `/admin_old` response point you toward?**

<details>
<summary>💡 Hint 1</summary>
The response references a course concept from a later stage — think about what other kind of "forgotten" surface exists on this server (hint: it's not a single endpoint, it's an entire API version).
</details>

---

## Flags to Find

| Flag   | Description                                              | Hint                                   |
|--------|-------------------------------------------------------------|-------------------------------------------|
| FLAG 1 | Three wordlist entries returning HTTP 200                    | Try backup/env/admin-themed words          |
| FLAG 2 | Backup filename + embedded flag string                       | Fuzz recursively inside `/backup`          |
| FLAG 3 | Confirm the leaked JWT secret matches the debug endpoint's    | `curl /.env`                               |
| FLAG 4 | What `/admin_old`'s hint points toward                        | Read the JSON response's "hint" field      |

---

## Remediation

### 1. Don't Rely on Filtering a Listing as Protection
```python
# ❌ False sense of security
"registered_routes": [r for r in routes if not r.startswith("hidden")]

# ✅ Actually remove or gate the endpoint
@app.before_request
def block_backup_paths():
    if request.path.startswith(("/backup", "/.env", "/admin_old")):
        return jsonify({"error": "Not found"}), 404
```

### 2. Never Store Backups or `.env` Files in the Web Root
- Keep backups outside any publicly served directory entirely.
- Add `.env`, `*.bak`, `*.old`, `*.sql` to deployment exclude rules.

### 3. Block at the Web Server / Reverse Proxy Layer
```nginx
location ~ /\.(env|git) { deny all; return 404; }
location ~ \.(bak|old|sql)$ { deny all; return 404; }
```

### 4. Actually Decommission Prototype/Staging Endpoints
- If a prototype admin panel is "scheduled for removal," track that as a real ticket with a deadline, not a comment in code.

---

## References

- [OWASP API Security Top 10 - API9:2023](https://owasp.org/API-Security/editions/2023/en/0xa9-improper-inventory-management/)
- [CWE-530: Exposure of Backup File to an Unauthorized Control Sphere](https://cwe.mitre.org/data/definitions/530.html)
- [ffuf documentation](https://github.com/ffuf/ffuf)
- [gobuster documentation](https://github.com/OJ/gobuster)

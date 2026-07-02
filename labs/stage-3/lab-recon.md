# Lab 01: API Reconnaissance

## Overview

| Field          | Details                                      |
|----------------|----------------------------------------------|
| **Objective**  | Discover and enumerate all API endpoints      |
| **Difficulty** | ⭐ Easy                                      |
| **Time**       | 30 minutes                                   |
| **Category**   | Reconnaissance / Information Gathering        |
| **OWASP**      | API9:2023 - Improper Inventory Management     |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5000`
- `curl` or an HTTP client (Postman, Burp Suite, etc.)
- Python 3 with the `requests` library installed
- Basic understanding of HTTP methods and REST APIs

---

## Background

API reconnaissance is the first phase of any API security assessment. Before you can test for vulnerabilities, you need to understand what endpoints exist, what technologies are in use, and what information the API reveals about itself.

Many APIs expose more information than intended — debug endpoints, stack traces, version headers, and framework details can all give an attacker a significant advantage. A well-configured production API should reveal as little as possible about its internals.

In this lab, you will explore the SocialHack API to discover its structure, find hidden endpoints, and extract sensitive configuration details.

---

## Tasks

### Task 1: Access the Root Endpoint

Start by exploring what the API reveals at its root URL.

**Steps:**
1. Send a GET request to `http://localhost:5000/`
2. Examine the response for API name, version, and description
3. Note any links or references to documentation

**curl example:**
```bash
curl -s http://localhost:5000/ | python3 -m json.tool
```

**Python example:**
```python
import requests

response = requests.get("http://localhost:5000/")
print(response.json())
```

<details>
<summary>💡 Hint 1</summary>
The root endpoint usually returns a welcome message or API overview.
</details>

<details>
<summary>💡 Hint 2</summary>
Look at the response JSON for fields like "version", "name", or "docs".
</details>

<details>
<summary>💡 Hint 3</summary>
The response should reveal the API version (v1) and possibly a link to documentation or a list of available routes.
</details>

---

### Task 2: Find the Debug Endpoint

Many frameworks include debug or diagnostic endpoints that should be disabled in production. Try to find one.

**Steps:**
1. Try common debug/diagnostic paths: `/debug`, `/api/debug`, `/api/v1/debug`
2. Examine the response for sensitive configuration details
3. Note what kind of information is exposed

**curl example:**
```bash
curl -s http://localhost:5000/api/v1/debug | python3 -m json.tool
```

<details>
<summary>💡 Hint 1</summary>
Debug endpoints often follow the API path convention. If the API base is /api/v1/, try /api/v1/debug.
</details>

<details>
<summary>💡 Hint 2</summary>
The debug endpoint might expose environment variables, configuration, or secret keys.
</details>

<details>
<summary>💡 Hint 3</summary>
Send a GET request to <code>http://localhost:5000/api/v1/debug</code>. Look for a field containing the JWT secret key in the JSON response.
</details>

---

### Task 3: Extract the JWT Secret Key

The debug endpoint contains critical security information. Find the JWT signing secret.

**Steps:**
1. Parse the debug endpoint response carefully
2. Look for fields related to JWT, tokens, or secrets
3. Document the exact secret key value

**🚩 FLAG 1: What is the JWT secret key?**

<details>
<summary>💡 Hint 1</summary>
The JWT secret is used to sign authentication tokens. It is often stored in config.
</details>

<details>
<summary>💡 Hint 2</summary>
Look for a key like "jwt_secret", "secret_key", or "JWT_SECRET_KEY" in the debug output.
</details>

<details>
<summary>💡 Hint 3</summary>
The secret key is: <code>socialhack-secret-key</code>
</details>

---

### Task 4: List All Registered Routes

Discover all available API endpoints to map the attack surface.

**Steps:**
1. Check the debug endpoint for a list of registered routes
2. Alternatively, check common documentation paths: `/api/v1/docs`, `/api/v1/routes`
3. Count the total number of registered routes

**🚩 FLAG 2: How many registered routes does the API have?**

<details>
<summary>💡 Hint 1</summary>
The debug endpoint may include a "routes" field listing all registered endpoints.
</details>

<details>
<summary>💡 Hint 2</summary>
Iterate through the routes list and count them. Include all HTTP methods.
</details>

<details>
<summary>💡 Hint 3</summary>
Parse the "routes" array from the debug endpoint and count the total elements. You can use: <code>len(response.json()["routes"])</code>
</details>

---

### Task 5: Identify Server Environment Details

Determine the programming language, framework, and Python version.

**Steps:**
1. Check response headers for server information (e.g., `Server`, `X-Powered-By`)
2. Examine the debug endpoint for environment details
3. Note the Python version running on the server

**🚩 FLAG 3: What Python version is the server running?**

<details>
<summary>💡 Hint 1</summary>
Response headers sometimes include framework or language information. Check the "Server" header.
</details>

<details>
<summary>💡 Hint 2</summary>
The debug endpoint may include a field like "python_version" or "environment".
</details>

<details>
<summary>💡 Hint 3</summary>
Look for a "python_version" or "server_info" field in the debug endpoint's JSON response.
</details>

---

## Flags to Find

| Flag   | Description                          | Hint                           |
|--------|--------------------------------------|--------------------------------|
| FLAG 1 | The JWT secret key                   | Found in the debug endpoint    |
| FLAG 2 | The number of registered routes      | Count from the routes list     |
| FLAG 3 | The Python version on the server     | Found in debug or headers      |

---

## Remediation

After completing this lab, consider the following fixes:

### 1. Remove Debug Endpoints in Production
```python
# Only enable debug routes in development
if app.config["ENV"] == "development":
    app.register_blueprint(debug_bp)
```

### 2. Remove Sensitive Headers
```python
@app.after_request
def remove_headers(response):
    response.headers.pop("Server", None)
    response.headers.pop("X-Powered-By", None)
    return response
```

### 3. Use Environment Variables for Secrets
```python
import os
JWT_SECRET = os.environ.get("JWT_SECRET")
# Never hardcode or expose secrets
```

### 4. Implement Proper Inventory Management
- Maintain a registry of all API endpoints
- Regularly audit for unintended exposure
- Use API gateways to control access to internal endpoints
- Disable route listing in production

### 5. OWASP Recommendations
- **API9:2023 - Improper Inventory Management**: Maintain an up-to-date inventory of all API hosts and integrated services. Ensure all API versions are documented and deprecated properly.

---

## References

- [OWASP API Security Top 10 - API9:2023](https://owasp.org/API-Security/editions/2023/en/0xa9-improper-inventory-management/)
- [API Reconnaissance Techniques](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/)
- [NIST SP 800-95: Guide to Secure Web Services](https://csrc.nist.gov/publications/detail/sp/800-95/final)

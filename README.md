# 🔓 SocialHack API - Complete API Hacking Course: From Zero to Hero

> A vulnerable social media API designed for practical API security training.
> 
> Built according to the OWASP API Security Top 10 standards.

⚠️ **Warning**: This application is strictly for **educational purposes only**. Do not deploy it in a production environment.

## 📖 Course Overview

This course is structured into **8 stages**, taking you from basic concepts to mastery.

|**Stage**|**Name**|**Content**|
|---|---|---|
|🟢 **Stage 1**|Introduction to APIs|API basics, HTTP, API Types|
|🟢 **Stage 2**|Lab Setup|Postman, Burp Suite, Environment Configuration, jq Practical Usage, SocialHack Web UI|
|🟡 **Stage 3**|API Reconnaissance|Recon, OSINT, Endpoint Discovery, OpenAPI/Swagger Recon, ffuf/gobuster Fuzzing, nuclei Custom Templates|
|🟡 **Stage 4**|OWASP Top 10 (Part 1)|BOLA, Broken Auth, Mass Assignment|
|🔴 **Stage 5**|OWASP Top 10 (Part 2)|Rate Limiting, Rate-Limit Bypass, BFLA, Security Misconfig|
|🔴 **Stage 6**|Advanced Attacks|SQLi, NoSQLi, CMDi, SSRF, JWT, sqlmap Automation|
|⚫ **Stage 7**|Professional Mastery|GraphQL (+ Advanced Attacks), WebSocket Security, API Gateway Misconfiguration, Full Pentest, Defense Strategies|
|⚫ **Stage 8**|Additional OWASP Coverage|Unrestricted Business Flows (API6), Improper Inventory Management (API9), Unsafe Consumption of APIs (API10)|

## 🚀 Quick Setup

###  jq (JSON Processor - Optional but Recommended)

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq
```

Bash

```
# Install dependencies
cd api-hacking
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the API (auto-seeds database)
python3 run.py

# Reset database
python3 run.py --reset
```

API URL: `http://localhost:5001`
Web UI: `http://localhost:5001/app`

> `requirements.txt` includes `Flask-Sock` and `websocket-client` for the Stage 7.6 WebSocket chat lab — installed automatically by `pip install -r requirements.txt`, no extra step needed.

### 🖥️ SocialHack Web UI

A real, click-through social media frontend now lives at `/app` — register or log in with the test credentials below, land on a profile page, browse the feed, post, comment, follow, message, and (for the `admin` account) manage users. It's a plain Flask + Jinja2 server-rendered shell with vanilla JS — no build step, no extra dependencies.

**The UI itself has zero intentional vulnerabilities.** Every click/form submit calls the same `/api/v1/*` JSON API documented below via `fetch()`, so pointing Burp Suite (or your browser's DevTools Network tab) at the browser and clicking around surfaces the exact same requests you've been crafting by hand with curl/Postman throughout this course — see Tutorial 2.5. Action buttons (edit/delete, the "Admin" nav link) are only shown when the logged-in user "should" see them client-side, but since the underlying API endpoints mostly don't enforce that server-side either, navigating directly (e.g. typing `/app/admin` or `/app/profile/<id>` into the URL bar) reproduces the course's BOLA/BFLA lessons through the UI itself.

### 📄 Cheat Sheets & Quizzes

- `cheatsheets/stage-N-cheatsheet.md` — 1-page curl/payload quick reference per stage (1–8)
- `quizzes/stage-N-quiz.md` — 5-8 MCQ checkpoint quiz per stage, answers hidden in `<details>` blocks
- `nuclei-templates/*.yaml` — custom nuclei templates targeting this app's own vulnerabilities (Tutorial 3.6)

## 🔑 Test Credentials

|**Username**|**Password**|**Role**|**Notes**|
|---|---|---|---|
|alice|password123|user|Regular user|
|bob|password123|user|Regular user|
|charlie|password123|user|Private account 🔒|
|admin|admin123|admin|Platform admin|
|diana|diana2024!|moderator|Content moderator|

## 🌐 API Endpoints

**Base URL:** `http://localhost:5001`

### Authentication

Plaintext

```
POST /api/v1/auth/register        Register new user
POST /api/v1/auth/login           Login
POST /api/v1/auth/reset-password  Request password reset
POST /api/v1/auth/refresh         Refresh JWT token
```

### Users

Plaintext

```
GET/PUT/DELETE /api/v1/users/:id        User profile CRUD
GET    /api/v1/users/search?q=          Search users (SQLi!)
GET    /api/v1/users/:id/followers      Get followers
POST   /api/v1/users/:id/follow         Follow user
```

### Posts & Comments

Plaintext

```
GET/POST    /api/v1/posts              List/Create posts
GET/PUT/DEL /api/v1/posts/:id          Post CRUD
POST        /api/v1/posts/:id/like     Like a post
GET/POST    /api/v1/posts/:id/comments Comments
```

### Messages

Plaintext

```
GET  /api/v1/messages/:id                  Get message (BOLA!)
POST /api/v1/messages                      Send message
GET  /api/v1/messages/conversation/:uid    Get conversation
GET  /api/v1/messages/inbox                Inbox
```

### Admin

Plaintext

```
GET    /api/v1/admin/users           List all users (BFLA!)
DELETE /api/v1/admin/users/:id       Delete user
GET    /api/v1/admin/stats           Platform stats
PUT    /api/v1/admin/users/:id/role  Change role
```

### Tools (Command Injection!)

Plaintext

```
POST /api/v1/tools/ping          Ping a host (CMDi!)
POST /api/v1/tools/dns-lookup    DNS lookup (CMDi!)
POST /api/v1/tools/user-lookup   User lookup (NoSQLi!)
```

### GraphQL

Plaintext

```
GET/POST /api/v1/graphql         GraphQL endpoint (Introspection!)
```

### Webhooks

Plaintext

```
POST /api/v1/webhook/register      Register webhook (SSRF!)
POST /api/v1/webhook/test/:id      Test webhook
GET  /api/v1/webhook/list          List all webhooks
```

### Promotions (Unrestricted Business Flows!)

Plaintext

```
GET  /api/v1/promotions/verification/eligibility        Check verified-badge eligibility
POST /api/v1/promotions/verification/apply               Apply for badge (auto-approved, no rate limit!)
POST /api/v1/promotions/verification/revoke/:user_id      Revoke badge (BOLA!)
```

### Integrations (Unsafe Consumption of APIs!)

Plaintext

```
POST /api/v1/integrations/import-profile     Import profile from partner URL (blind trust, mass assignment!)
GET  /api/v1/integrations/exchange-rate      Fetch rate from provider URL (unchecked numeric value!)
```

### Legacy API (Improper Inventory Management — undocumented on purpose!)

Plaintext

```
GET  /api/v0/users              Full user dump, NO AUTH
GET  /api/v0/users/:id          Single user dump, NO AUTH
PUT  /api/v0/users/:id          Mass assignment, NO AUTH
GET  /api/v0/export-all         Full DB dump (users+posts+messages), NO AUTH
```

### OTP (Rate-Limit Bypass!)

Plaintext

```
POST /api/v1/otp/request     Request OTP code (limited: 3/60s, keyed on spoofable X-Forwarded-For!)
POST /api/v1/otp/verify      Verify OTP code
```

### Gateway-Protected Internal Stats (Simulated Gateway Misconfiguration!)

Plaintext

```
GET  /api/v1/gateway-internal/stats     Blocked without X-Gateway-Verified header (bypassable 3 ways!)
GET  /api/v1/internal/infra-stats       Undocumented alias — same data, no protection at all!
```

### WebSocket Chat (Cross-Site WebSocket Hijacking!)

Plaintext

```
WS   /ws/chat?room=<id>&token=<optional>     No Origin check, auth is cosmetic, any room joinable
```

### Hidden — Fuzzing Practice Targets (instructor reference only — filtered out of /api/v1/debug!)

Plaintext

```
GET  /backup                                      Directory listing (autoindex-style)
GET  /backup/socialhack_db_2024.sql.bak           Leaked DB backup file
GET  /.env                                        Leaked environment file (real JWT secret!)
GET  /admin_old                                   Forgotten staging admin prototype
```

### Upload & Export

Plaintext

```
POST /api/v1/upload/avatar    Upload avatar via URL (SSRF!)
GET  /api/v1/export/profile   Export profile (Info Disclosure!)
```

### Web UI (real click-through frontend, no vulnerabilities of its own!)

Plaintext

```
GET  /app                                  Redirects to feed or login
GET  /app/register, /app/login             Auth forms
GET  /app/feed                             Post feed, create post, like
GET  /app/profile/:id                      Profile view/edit, follow/unfollow
GET  /app/post/:id                         Post detail + comments
GET  /app/messages                         Inbox/sent, compose
GET  /app/messages/conversation/:id        Conversation view
GET  /app/admin                            User list, stats, role mgmt (nav-hidden but not server-protected!)
```

### Debug & Documentation (Undocumented on purpose!)

Plaintext

```
GET  /                 API info (Info Disclosure!)
GET  /api/v1/debug     Debug info (JWT secret leaked!)
GET  /openapi.json     Auto-generated spec (leaks admin/debug/tools/legacy paths!)
GET  /swagger          HTML docs viewer for the same leaked spec
```


## 🛡️ Embedded Vulnerabilities (22 Types)

|**#**|**Vulnerability**|**OWASP Category**|**Endpoint Example**|
|---|---|---|---|
|1|BOLA/IDOR|API1:2023|users, messages, posts|
|2|Broken Authentication|API2:2023|auth/login, reset|
|3|Excessive Data Exposure|API3:2023|export/profile|
|4|No Rate Limiting|API4:2023|posts/like, auth/login|
|5|Broken Function Level Auth|API5:2023|admin/*|
|6|Mass Assignment|API3:2023|auth/register, users|
|7|SSRF|API7:2023|upload/avatar, webhooks|
|8|Security Misconfiguration|API8:2023|CORS, debug mode|
|9|SQL Injection|—|users/search|
|10|NoSQL-style Injection|—|tools/user-lookup|
|11|Command Injection|—|tools/ping, dns-lookup|
|12|JWT Weakness|—|Auth (weak secret, none alg)|
|13|Race Condition|—|posts/like|
|14|Predictable Tokens|—|auth/reset-password|
|15|GraphQL Attacks (introspection, alias abuse, batch DoS, persisted-query bypass)|—|graphql (introspection, alias, batch array, persisted-query fallthrough)|
|16|CORS Misconfiguration|—|All endpoints|
|17|Unrestricted Business Flows|API6:2023|promotions/verification/apply|
|18|Improper Inventory Management|API9:2023|/api/v0/* (undocumented legacy API), /openapi.json (leaked internal paths)|
|19|Unsafe Consumption of APIs|API10:2023|integrations/import-profile|
|20|Rate-Limit Bypass (spoofable trust header)|API4:2023|otp/request (X-Forwarded-For spoofing)|
|21|Cross-Site WebSocket Hijacking (no Origin check, cosmetic auth)|API2:2023|ws/chat|
|22|API Gateway Misconfiguration (trailing-slash, route alias, spoofable header)|API8:2023|gateway-internal/stats, internal/infra-stats|

> 📝 **Correction (Stage 8 update):** row #6 (Mass Assignment) was previously mislabeled `API6:2023`
> in this table — it has been corrected to `API3:2023 - Broken Object Property Level Authorization`,
> which is its actual category in the OWASP API Security Top 10 (2023). `API6:2023` is
> `Unrestricted Access to Sensitive Business Flows`, now covered separately by #17 above.

## ⚖️ Disclaimer

This project is created strictly for **educational purposes**. Unauthorized hacking of external systems is **illegal**. Always adhere to ethical hacking principles and obtain proper authorization before testing any systems.
# 🔓 SocialHack API - Complete API Hacking Course: From Zero to Hero

> A vulnerable social media API designed for practical API security training.
> 
> Built according to the OWASP API Security Top 10 standards.

⚠️ **Warning**: This application is strictly for **educational purposes only**. Do not deploy it in a production environment.

## 📖 Course Overview

This course is structured into **8 stages**, taking you from basic concepts to mastery.

<table><tbody><tr><th>**Stage**</th><th>**Name**</th><th>**Content**</th></tr>
<tr><td>🟢 **Stage 1**</td><td>Introduction to APIs</td><td>API basics, HTTP, API Types</td></tr>
<tr><td>🟢 **Stage 2**</td><td>Lab Setup</td><td>Postman, Burp Suite, Environment Configuration, jq Practical Usage, SocialHack Web UI</td></tr>
<tr><td>🟡 **Stage 3**</td><td>API Reconnaissance</td><td>Recon, OSINT, Endpoint Discovery, OpenAPI/Swagger Recon, ffuf/gobuster Fuzzing, nuclei Custom Templates</td></tr>
<tr><td>🟡 **Stage 4**</td><td>OWASP Top 10 (Part 1)</td><td>BOLA, Broken Auth, Mass Assignment</td></tr>
<tr><td>🔴 **Stage 5**</td><td>OWASP Top 10 (Part 2)</td><td>Rate Limiting, Rate-Limit Bypass, BFLA, Security Misconfig</td></tr>
<tr><td>🔴 **Stage 6**</td><td>Advanced Attacks</td><td>SQLi, NoSQLi, CMDi, SSRF, JWT, sqlmap Automation</td></tr>
<tr><td>⚫ **Stage 7**</td><td>Professional Mastery</td><td>GraphQL (+ Advanced Attacks), WebSocket Security, API Gateway Misconfiguration, Full Pentest, Defense Strategies</td></tr>
<tr><td>⚫ **Stage 8**</td><td>Additional OWASP Coverage</td><td>Unrestricted Business Flows (API6), Improper Inventory Management (API9), Unsafe Consumption of APIs (API10)</td></tr>
<tr><td>🆕 **Beyond the Lab**</td><td>Modern API Attack Surface</td><td>OAuth2/OIDC flow attacks, Mobile hardcoded secrets, gRPC security, Supply-chain (SCA), AI/LLM API security, MCP tool-call security (see the "Beyond the Lab" section below)</td></tr>
</tbody>
</table>

## 🚀 Quick Setup

### jq (JSON Processor - Optional but Recommended)

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq
```

For Kali & Debian users

```
sudo apt install -y libxml2-dev libxslt1-dev python3-dev build-essential 
```

Initial Setup

```
# Clone & Install dependencies 
git clone https://github.com/KhitMinnyo/SocialHackAPI.git
cd SocialHackAPI
python3 -m venv venv 
source venv/bin/activate
pip install flask #for Kali & Debians
pip install -r requirements.txt

# Start the API (auto-seeds database)
python3 run.py --reset
```

Re-run app

```
cd SocialHackAPI 
source venv/bin/activate
# Reset database 
python3 run.py --reset
```

API URL: `http://localhost:5001`  
Web UI: `http://localhost:5001/app`

> `requirements.txt` includes `Flask-Sock` and `websocket-client` for the Stage 7.6 WebSocket chat lab — installed automatically by `pip install -r requirements.txt`, no extra step needed.

### 🖥️ SocialHack Web UI

A real, click-through social media frontend now lives at `/app` — register or log in with the test credentials below, land on a profile page, browse the feed, post, comment, follow, message, and (for the `admin` account) manage users. It's a plain Flask + Jinja2 server-rendered shell with vanilla JS — no build step, no extra dependencies.

**The UI itself has zero intentional vulnerabilities.** Every click/form submit calls the same `/api/v1/*` JSON API documented below via `fetch()`, so pointing Burp Suite (or your browser's DevTools Network tab) at the browser and clicking around surfaces the exact same requests you've been crafting by hand with curl/Postman throughout this course — see Tutorial 2.5. Action buttons (edit/delete, the "Admin" nav link) are only shown when the logged-in user "should" see them client-side, but since the underlying API endpoints mostly don't enforce that server-side either, navigating directly (e.g. typing `/app/admin` or `/app/profile/<id>` into the URL bar) reproduces the course's BOLA/BFLA lessons through the UI itself.

### 📄 Cheat Sheets

-   `cheatsheets/stage-N-cheatsheet.md` — 1-page curl/payload quick reference per stage (1–8)
    
-   `cheatsheets/beyond-lab-xss-oauth-cheatsheet.md` — stored-XSS token theft + OAuth contact-spam walkthrough
    
-   `nuclei-templates/*.yaml` — custom nuclei templates targeting this app's own vulnerabilities (Tutorial 3.6)
    

## 🔑 Test Credentials

<table><tbody><tr><th>**Username**</th><th>**Password**</th><th>**Role**</th><th>**Notes**</th></tr>
<tr><td>alice</td><td>password123</td><td>user</td><td>Regular user</td></tr>
<tr><td>bob</td><td>password123</td><td>user</td><td>Regular user</td></tr>
<tr><td>charlie</td><td>password123</td><td>user</td><td>Private account 🔒</td></tr>
<tr><td>admin</td><td>admin123</td><td>admin</td><td>Platform admin</td></tr>
<tr><td>diana</td><td>diana2024!</td><td>moderator</td><td>Content moderator</td></tr>
</tbody>
</table>

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

### 🆕 Beyond the Lab — Modern API Attack Surface

These are **new extensions** added on top of the original 8-stage course, covering  
current API-security topics the core REST/GraphQL/WebSocket labs don't touch.

#### OAuth2 / OIDC Authorization Server (vulnerable flows!)

Plaintext

```
GET  /oauth/authorize     Authorization Code flow (loose redirect_uri = code theft!)
POST /oauth/token         Exchange code -> full API token (no PKCE/client_secret enforce, code replay!)
GET  /oauth/userinfo      OIDC userinfo (no scope enforcement)
```

> Registered client: `socialhack-mobile`. The resource owner is identified for lab  
> purposes by an existing SocialHack JWT (`?token=` or `Authorization: Bearer`).  
> Add `&debug=1` to `/oauth/authorize` to get the code as JSON instead of a 302.

#### Mobile Client Config (hardcoded secrets!)

Plaintext

```
GET  /mobile/config                     Runtime config with shipped secrets (client_secret, master key!)
GET  /.well-known/mobile-config.json    Same config, conventional path (fuzzable)
GET  /mobile/strings.xml                Simulated apktool-recovered Android strings.xml
```

#### AI / LLM Assistant (prompt injection, OWASP LLM Top 10!)

Plaintext

```
POST /api/v1/assistant/chat   Mock LLM assistant (prompt injection, system-prompt leak,
                              excessive agency -> BOLA via prose, insecure output). No API key needed.
```

#### gRPC Service (auto-starts on :50051 — see `grpc-lab/`)

```
UserService @ :50051   GetUser / ListUsers (no auth), DeleteUser (spoofable role metadata),
                       server reflection ON, no TLS
```

The gRPC deps are now in the main `requirements.txt`, so `python run.py`**  
auto-starts this service on :50051** alongside the REST API (compiling the stubs  
on first run) — no extra steps:

```
pip install -r requirements.txt   # already includes grpcio
python run.py                      # REST :5001 + gRPC :50051
```

Disable the auto-start with `SOCIALHACK_GRPC=0`. To run standalone instead, see `grpc-lab/README.md`.

#### Supply-Chain Scanning Lab (see `supply-chain-lab/`)

```
supply-chain-lab/requirements-vulnerable.txt   Known-CVE pinned deps for SCA scanning
                                               (pip-audit / safety / Trivy)
```

Scan: `pip install pip-audit && pip-audit --no-deps -r supply-chain-lab/requirements-vulnerable.txt`

#### MCP (Model Context Protocol) Server (tool-call BOLA + tool description poisoning!)

```
POST /api/v1/mcp             JSON-RPC 2.0 (initialize / tools/list / tools/call)
POST /api/v1/mcp/agent-demo  Lab-only helper - simulates a naive MCP client agent
```

Hand-rolled MCP server (`app/routes/mcp_tools.py`, no external MCP SDK) exposing three  
tools. `get_user_profile` takes a caller-supplied `user_id` argument with no ownership  
check (BOLA, same bug class as `users.py`, reached via a tool-call argument instead of a  
URL segment). `summarize_post`'s **description** field (the metadata an MCP client's LLM  
reads to decide how to use a tool) contains a hidden instruction telling the agent to  
silently also call `get_user_profile` on the admin account and exfiltrate its `api_key` -  
tool description poisoning, a.k.a. "line jumping". `/api/v1/mcp/agent-demo` plays the role  
of a naive tool-description-trusting client (the same honesty trade-off as  
`ai_assistant.py`'s prompt-injection stub) so the poisoning is provable without a real LLM.

#### Stored XSS → Session/Token Theft Lab (self-contained, isolated from `/app`!)

```
POST /api/v1/xss-lab/widgets            Post a "guestbook" widget (unescaped content!)
GET  /api/v1/xss-lab/widgets/:id        Raw JSON view of a widget
GET  /xss-lab/widget/:id                Renders the widget - the page a "victim" opens
POST /api/v1/xss-lab/collect            Unauthenticated "attacker collector" (no real infra needed)
GET  /xss-lab/attacker-dashboard        Shows everything the collector has received
```

`app/routes/xss_lab.py` teaches the mechanism behind the very common real-world pattern  
of a hijacked session on a messaging platform: a widget's `content` is rendered with  
Jinja2's `| safe` filter (no escaping), so an attacker-authored `<script>` executes for  
whoever opens `/xss-lab/widget/:id`. Because SocialHack's JWT lives in `localStorage`  
(see `static/js/app.js`) and this lab shares the same origin as `/app`, the injected  
script can read `localStorage.getItem('socialhack_token')` and POST it to  
`/api/v1/xss-lab/collect` — an in-app stand-in for an attacker's own server, so the full  
injection → exfiltration → reuse chain works with zero external infrastructure and zero  
real user data. Deliberately kept **out** of `/app/*`, which stays free of intentional  
vulnerabilities (see `app/routes/web.py`'s docstring). See  
`cheatsheets/beyond-lab-xss-oauth-cheatsheet.md` for the full walkthrough, including how  
a stolen/over-scoped token feeds directly into the OAuth contact-spam lab below.

#### OAuth Contact-Spam Lab (malicious 3rd-party app abusing granted scope)

Extends the OAuth2/OIDC server above with a second registered client in  
`OAUTH_CLIENTS` (`app/routes/oauth.py`):

```
quizapp-fun-2000   "Which SocialHack Personality Are You?" Quiz (unverified 3rd-party app)
```

No new backend vulnerability is needed — it reuses vulnerability #6 above (requested  
`scope` is trusted blindly, no real consent screen) plus the existing `messages` BOLA  
(no rate limit, no privacy check) to demonstrate exactly why a scammy Discord/Facebook  
"quiz" or bot app can message a victim's entire contact list within seconds of being  
authorized: get a token via `/oauth/authorize` + `/oauth/token`, list the victim's  
followers via `GET /api/v1/users/:id/followers`, then loop `POST /api/v1/messages`  
against every one of them. Full runnable walkthrough in  
`cheatsheets/beyond-lab-xss-oauth-cheatsheet.md`.

## 🛡️ Embedded Vulnerabilities (38 Types)

<table><tbody><tr><th>**#**</th><th>**Vulnerability**</th><th>**OWASP Category**</th><th>**Endpoint Example**</th></tr>
<tr><td>1</td><td>BOLA/IDOR</td><td>API1:2023</td><td>users, messages, posts</td></tr>
<tr><td>2</td><td>Broken Authentication</td><td>API2:2023</td><td>auth/login, reset</td></tr>
<tr><td>3</td><td>Excessive Data Exposure</td><td>API3:2023</td><td>export/profile</td></tr>
<tr><td>4</td><td>No Rate Limiting</td><td>API4:2023</td><td>posts/like, auth/login</td></tr>
<tr><td>5</td><td>Broken Function Level Auth</td><td>API5:2023</td><td>admin/\*</td></tr>
<tr><td>6</td><td>Mass Assignment</td><td>API3:2023</td><td>auth/register, users</td></tr>
<tr><td>7</td><td>SSRF</td><td>API7:2023</td><td>upload/avatar, webhooks</td></tr>
<tr><td>8</td><td>Security Misconfiguration</td><td>API8:2023</td><td>CORS, debug mode</td></tr>
<tr><td>9</td><td>SQL Injection</td><td>—</td><td>users/search</td></tr>
<tr><td>10</td><td>NoSQL-style Injection</td><td>—</td><td>tools/user-lookup</td></tr>
<tr><td>11</td><td>Command Injection</td><td>—</td><td>tools/ping, dns-lookup</td></tr>
<tr><td>12</td><td>JWT Weakness</td><td>—</td><td>Auth (weak secret, none alg)</td></tr>
<tr><td>13</td><td>Race Condition</td><td>—</td><td>posts/like</td></tr>
<tr><td>14</td><td>Predictable Tokens</td><td>—</td><td>auth/reset-password</td></tr>
<tr><td>15</td><td>GraphQL Attacks (introspection, alias abuse, batch DoS, persisted-query bypass)</td><td>—</td><td>graphql (introspection, alias, batch array, persisted-query fallthrough)</td></tr>
<tr><td>16</td><td>CORS Misconfiguration</td><td>—</td><td>All endpoints</td></tr>
<tr><td>17</td><td>Unrestricted Business Flows</td><td>API6:2023</td><td>promotions/verification/apply</td></tr>
<tr><td>18</td><td>Improper Inventory Management</td><td>API9:2023</td><td>/api/v0/\* (undocumented legacy API), /openapi.json (leaked internal paths)</td></tr>
<tr><td>19</td><td>Unsafe Consumption of APIs</td><td>API10:2023</td><td>integrations/import-profile</td></tr>
<tr><td>20</td><td>Rate-Limit Bypass (spoofable trust header)</td><td>API4:2023</td><td>otp/request (X-Forwarded-For spoofing)</td></tr>
<tr><td>21</td><td>Cross-Site WebSocket Hijacking (no Origin check, cosmetic auth)</td><td>API2:2023</td><td>ws/chat</td></tr>
<tr><td>22</td><td>API Gateway Misconfiguration (trailing-slash, route alias, spoofable header)</td><td>API8:2023</td><td>gateway-internal/stats, internal/infra-stats</td></tr>
<tr><td>23</td><td>OAuth2 redirect\_uri manipulation (code theft)</td><td>—</td><td>oauth/authorize</td></tr>
<tr><td>24</td><td>OAuth2 code replay / no PKCE / no client auth</td><td>—</td><td>oauth/token</td></tr>
<tr><td>25</td><td>Hardcoded secrets in mobile client</td><td>—</td><td>mobile/config, mobile/strings.xml</td></tr>
<tr><td>26</td><td>gRPC no-auth + reflection + spoofable metadata trust</td><td>—</td><td>grpc-lab (UserService @ :50051)</td></tr>
<tr><td>27</td><td>Vulnerable dependencies (supply chain)</td><td>—</td><td>supply-chain-lab/requirements-vulnerable.txt</td></tr>
<tr><td>28</td><td>LLM Prompt Injection + System-Prompt Leak</td><td>LLM01/LLM07</td><td>assistant/chat</td></tr>
<tr><td>29</td><td>LLM Excessive Agency (BOLA via prose)</td><td>LLM08</td><td>assistant/chat</td></tr>
<tr><td>30</td><td>LLM Insecure Output Handling</td><td>LLM02</td><td>assistant/chat</td></tr>
<tr><td>31</td><td>MCP Tool-Call Authorization Bypass (BOLA via tool arguments)</td><td>—</td><td>mcp (get\_user\_profile)</td></tr>
<tr><td>32</td><td>MCP Tool Description Poisoning ("line jumping")</td><td>—</td><td>mcp (summarize\_post), mcp/agent-demo</td></tr>
<tr><td>33</td><td>Stored XSS → Session/Token Theft (unescaped render, token in localStorage)</td><td>API8:2023</td><td>xss-lab/widget/:id, xss-lab/collect</td></tr>
<tr><td>34</td><td>OAuth Excessive Scope Grant → Automated Contact/Message Spam</td><td>API6:2023</td><td>oauth (quizapp-fun-2000 client) + messages (no rate limit)</td></tr>
<tr><td>35</td><td>XXE Injection (file read / SSRF via XML entity)</td><td>—</td><td>integrations/xml-import (lxml resolve\_entities)</td></tr>
<tr><td>36</td><td>Path Traversal / Unrestricted File Upload</td><td>—</td><td>upload/document (client filename, no allowlist)</td></tr>
<tr><td>37</td><td>CSRF (cookie-session state-changing endpoint)</td><td>—</td><td>settings/update (no CSRF token / Origin check)</td></tr>
<tr><td>38</td><td>HPP / Content-Type Confusion (parser differential)</td><td>API8:2023</td><td>tools/report (duplicate scope param, form-encoded bypass)</td></tr>
</tbody>
</table>

> 🆕 **v2.0 book update:** rows #35–38 accompany the v2.0 book's new chapters  
> (23 XXE, 24 File Upload, 29 CSRF, 17.5 HPP/Content-Type Confusion) plus the  
> Authorization-Matrix additions to the BOLA/BFLA chapters and the Bug-Bounty  
> workflow in the Reporting chapter. All four new endpoints were live-tested  
> (2026-08-21) against the curl payloads printed in those chapters.

> 🆕 **Beyond-the-Lab update:** rows #23–34 are new modern-API extensions (OAuth2/OIDC,  
> mobile secrets, gRPC, supply chain, AI/LLM, MCP, stored XSS, OAuth scope abuse). LLM rows  
> map to the **OWASP Top 10 for LLM Applications** (a separate framework from the API  
> Security Top 10); MCP rows are a tool-call-layer variant of the existing BOLA (API1) and  
> prompt-injection concepts; #33–34 tie directly together (a stolen or over-scoped token  
> reused to mass-message a victim's contacts) and mirror how real account-takeover scams  
> spread on messaging platforms.

> 📝 **Correction (Stage 8 update):** row #6 (Mass Assignment) was previously mislabeled `API6:2023`  
> in this table — it has been corrected to `API3:2023 - Broken Object Property Level Authorization`,  
> which is its actual category in the OWASP API Security Top 10 (2023). `API6:2023` is  
> `Unrestricted Access to Sensitive Business Flows`, now covered separately by #17 above.

## ⚖️ Disclaimer

This project is created strictly for **educational purposes**. Unauthorized hacking of external systems is **illegal**. Always adhere to ethical hacking principles and obtain proper authorization before testing any systems.
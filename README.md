# 🔓 SocialHack API - Complete API Hacking Course: From Zero to Hero

> A vulnerable social media API designed for practical API security training.
> 
> Built according to the OWASP API Security Top 10 standards.

⚠️ **Warning**: This application is strictly for **educational purposes only**. Do not deploy it in a production environment.

## 📖 Course Overview

This course is structured into **7 stages**, taking you from basic concepts to mastery.

|**Stage**|**Name**|**Content**|
|---|---|---|
|🟢 **Stage 1**|Introduction to APIs|API basics, HTTP, API Types|
|🟢 **Stage 2**|Lab Setup|Postman, Burp Suite, Environment Configuration|
|🟡 **Stage 3**|API Reconnaissance|Recon, OSINT, Endpoint Discovery|
|🟡 **Stage 4**|OWASP Top 10 (Part 1)|BOLA, Broken Auth, Mass Assignment|
|🔴 **Stage 5**|OWASP Top 10 (Part 2)|Rate Limiting, BFLA, Security Misconfig|
|🔴 **Stage 6**|Advanced Attacks|SQLi, NoSQLi, CMDi, SSRF, JWT|
|⚫ **Stage 7**|Professional Mastery|GraphQL, Full Pentest, Defense Strategies|

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

### Upload & Export

Plaintext

```
POST /api/v1/upload/avatar    Upload avatar via URL (SSRF!)
GET  /api/v1/export/profile   Export profile (Info Disclosure!)
```

### Debug

Plaintext

```
GET  /                 API info (Info Disclosure!)
GET  /api/v1/debug     Debug info (JWT secret leaked!)
```


## 🛡️ Embedded Vulnerabilities (16 Types)

|**#**|**Vulnerability**|**OWASP Category**|**Endpoint Example**|
|---|---|---|---|
|1|BOLA/IDOR|API1:2023|users, messages, posts|
|2|Broken Authentication|API2:2023|auth/login, reset|
|3|Excessive Data Exposure|API3:2023|export/profile|
|4|No Rate Limiting|API4:2023|posts/like, auth/login|
|5|Broken Function Level Auth|API5:2023|admin/*|
|6|Mass Assignment|API6:2023|auth/register, users|
|7|SSRF|API7:2023|upload/avatar, webhooks|
|8|Security Misconfiguration|API8:2023|CORS, debug mode|
|9|SQL Injection|—|users/search|
|10|NoSQL-style Injection|—|tools/user-lookup|
|11|Command Injection|—|tools/ping, dns-lookup|
|12|JWT Weakness|—|Auth (weak secret, none alg)|
|13|Race Condition|—|posts/like|
|14|Predictable Tokens|—|auth/reset-password|
|15|GraphQL Attacks|—|graphql (introspection)|
|16|CORS Misconfiguration|—|All endpoints|

## ⚖️ Disclaimer

This project is created strictly for **educational purposes**. Unauthorized hacking of external systems is **illegal**. Always adhere to ethical hacking principles and obtain proper authorization before testing any systems.
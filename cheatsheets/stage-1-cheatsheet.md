# 🗂️ Cheat Sheet — Stage 1: Introduction to APIs

## HTTP Methods

| Method | Purpose | Idempotent? | Has body? |
|---|---|---|---|
| GET | Read data | ✅ | ❌ |
| POST | Create a new resource | ❌ | ✅ |
| PUT | Replace a resource | ✅ | ✅ |
| PATCH | Partially update a resource | ❌ | ✅ |
| DELETE | Delete a resource | ✅ | ❌ (usually) |

## HTTP Status Codes (Quick Reference)

| Code | Meaning | Security relevance |
|---|---|---|
| 200 | OK | — |
| 201 | Created | — |
| 400 | Bad Request | Verbose error → info disclosure |
| 401 | Unauthorized | Authentication is required |
| 403 | Forbidden | The endpoint exists, but access is denied |
| 404 | Not Found | The endpoint/resource is missing; compare with 403 during enumeration |
| 405 | Method Not Allowed | The endpoint exists, but the method is not supported |
| 429 | Too Many Requests | A rate limit was reached |
| 500 | Internal Server Error | Stack trace or database details may leak |

## Common Request Headers

```
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
X-Forwarded-For: 127.0.0.1        (IP spoofing / rate-limit bypass testing)
Origin: https://evil.com          (CORS testing)
```

## curl Quick Reference

```bash
# GET request
curl -s http://localhost:5001/api/v1/posts

# POST JSON body
curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'

# Authenticated request
curl -s http://localhost:5001/api/v1/users/1 \
  -H "Authorization: Bearer $TOKEN"

# Pretty-print JSON response
curl -s http://localhost:5001/ | jq .

# Show response headers only
curl -sI http://localhost:5001/
```

## API Types Quick Comparison

| | REST | GraphQL | SOAP |
|---|---|---|---|
| Data format | JSON (usually) | JSON | XML |
| Endpoint style | Many endpoints, per-resource | One endpoint | One endpoint |
| Query flexibility | Fixed shape per endpoint | Client chooses fields | Fixed by WSDL |
| Common vuln class | BOLA, mass assignment | Introspection, nested query DoS | XXE, WSDL disclosure |

---
*SocialHack API Hacking Course — Stage 1 Cheat Sheet*

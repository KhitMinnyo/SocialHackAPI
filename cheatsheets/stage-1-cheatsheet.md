# 🗂️ Cheat Sheet — Stage 1: Introduction to APIs

## HTTP Methods

| Method | ရည်ရွယ်ချက် | Idempotent? | Body ပါလား |
|---|---|---|---|
| GET | Data ယူခြင်း | ✅ | ❌ |
| POST | Resource အသစ် ဖန်တီးခြင်း | ❌ | ✅ |
| PUT | Resource တစ်ခုလုံး update | ✅ | ✅ |
| PATCH | Resource တစ်စိတ်တစ်ပိုင်း update | ❌ | ✅ |
| DELETE | Resource ဖျက်ခြင်း | ✅ | ❌ (usually) |

## HTTP Status Codes (Quick Reference)

| Code | အဓိပ္ပါယ် | Security အရ အရေးပါချက် |
|---|---|---|
| 200 | OK | — |
| 201 | Created | — |
| 400 | Bad Request | Verbose error → info disclosure |
| 401 | Unauthorized | Auth လိုအပ် |
| 403 | Forbidden | Endpoint ရှိတယ်၊ access မရ |
| 404 | Not Found | Endpoint မရှိ (403 vs 404 ခြားနားချက် — enumeration) |
| 405 | Method Not Allowed | Endpoint ရှိတယ်၊ method မှား |
| 429 | Too Many Requests | Rate limit ရှိကြောင်း |
| 500 | Internal Server Error | Stack trace/DB error ပေါက်နိုင် |

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

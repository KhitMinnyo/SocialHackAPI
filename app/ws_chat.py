"""WebSocket chat feature with intentional vulnerabilities.

Not a formal OWASP API Top 10 category, but WebSocket-specific security
issues are an extremely common real-world API surface that a pure
REST/GraphQL-focused course would otherwise skip entirely. See Stage 7.6.

VULNERABILITIES:
- No Origin header validation (Cross-Site WebSocket Hijacking / CSWSH):
  any website can open a WebSocket connection to this endpoint from a
  victim's browser, and the connection is accepted regardless of Origin.
  Browsers do NOT enforce the Same-Origin Policy for WebSocket connections
  the way they do for fetch()/XHR - it's entirely the server's job to
  check the Origin header, and this server doesn't.
- The `token` query parameter is OPTIONAL and, when present, is only used
  to derive a display name - it is never actually required for the
  connection to succeed, and the room-join logic never checks it either
  way. A fully unauthenticated client can connect and participate.
- No per-room authorization: any client can join ANY room just by naming
  it in the `room` query parameter, including rooms that represent
  private 1:1 conversations. This is the WebSocket equivalent of BOLA
  (API1:2023).
- Messages are broadcast to every socket currently in a room with no
  server-side filtering of who should be allowed to see what.
"""

import json
from flask import request
from app.utils import decode_token

# In-memory chat state: {room_id: set(ws_connection)}
_rooms = {}


def register_ws_routes(sock):
    """Register WebSocket routes against an already-initialized flask_sock.Sock."""

    @sock.route("/ws/chat")
    def chat_socket(ws):
        # VULNERABILITY: Origin is read but never validated against an
        # allowlist before accepting the connection (CSWSH).
        origin = request.headers.get("Origin", "")

        room_id = request.args.get("room", "general")
        token = request.args.get("token")

        # VULNERABILITY: token is optional and only cosmetic - it is
        # never required, and even when present its payload is trusted
        # without re-verifying the user still exists / still holds that
        # role, matching the same "trust the JWT payload" pattern used
        # elsewhere in this app (see app/utils/__init__.py: token_required).
        username = "anonymous"
        if token:
            payload = decode_token(token)
            if payload:
                username = f"user_{payload.get('user_id', 'unknown')}"

        # VULNERABILITY: no check that this client is actually a
        # participant of `room_id` - any client (including "anonymous")
        # can join ANY room, including ones meant to be private
        # conversations (e.g. ?room=dm-3-7).
        _rooms.setdefault(room_id, set()).add(ws)

        try:
            _broadcast(room_id, {
                "system": True,
                "message": f"{username} joined room '{room_id}' (origin={origin or 'none'})",
            })

            while True:
                raw = ws.receive()
                if raw is None:
                    break

                text = raw
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict) and "message" in parsed:
                        text = parsed["message"]
                except (ValueError, TypeError):
                    pass

                # VULNERABILITY: broadcasts to EVERY socket currently in
                # the room, including anyone who joined with no
                # authorization check above.
                _broadcast(room_id, {
                    "system": False,
                    "username": username,
                    "message": text,
                })
        finally:
            _rooms.get(room_id, set()).discard(ws)


def _broadcast(room_id, payload):
    dead = []
    body = json.dumps(payload)
    for conn in _rooms.get(room_id, set()):
        try:
            conn.send(body)
        except Exception:
            dead.append(conn)
    for conn in dead:
        _rooms[room_id].discard(conn)


def room_snapshot():
    """Debug helper: how many active connections per room (used by the lab's
    verification tooling, not exposed over HTTP)."""
    return {room: len(conns) for room, conns in _rooms.items()}

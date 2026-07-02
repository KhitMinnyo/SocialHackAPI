"""API documentation routes with intentional vulnerabilities.

OWASP API9:2023 - Improper Inventory Management (documentation angle)

Real teams often auto-generate an OpenAPI/Swagger spec from their route
table so frontend/partner developers always have an up-to-date reference.
The bug shows up when that generation process is NOT filtered before
publishing: internal-only, debug, admin, and even deprecated/legacy
endpoints get swept into the same public spec as the "real" documented
API surface.

This blueprint is intentionally NOT listed in the root "/" endpoint index
(app/__init__.py) - just like the /api/v1/debug endpoint - so it has to be
discovered the same way a real attacker would: recon/fuzzing, or simply
knowing that `/openapi.json` and `/swagger` are extremely common
conventions worth guessing.

VULNERABILITY: The generated spec below includes:
- Admin endpoints (app/routes/admin.py)
- The debug endpoint (/api/v1/debug) that leaks the JWT secret
- "Internal tool" endpoints that are vulnerable to command injection
  (app/routes/misc.py)
- The deprecated, unauthenticated /api/v0 legacy API (app/routes/legacy.py)

...none of which should ever appear in a spec meant for external/partner
developers. Each of those is tagged "internal" in the spec itself (a
realistic detail - someone DID try to mark them as internal - but nothing
in the publishing pipeline actually strips "internal"-tagged paths before
the spec is served publicly).
"""

from flask import Blueprint, jsonify, Response

docs_bp = Blueprint("docs", __name__)

# Each entry: (method, path, tag, summary, internal_only)
_ENDPOINTS = [
    # ---- Documented / intended public surface ----
    ("POST", "/api/v1/auth/register", "auth", "Register a new user", False),
    ("POST", "/api/v1/auth/login", "auth", "Login and receive a JWT", False),
    ("POST", "/api/v1/auth/reset-password", "auth", "Request a password reset token", False),
    ("POST", "/api/v1/auth/reset-password/confirm", "auth", "Confirm password reset", False),
    ("POST", "/api/v1/auth/refresh", "auth", "Refresh a JWT token", False),
    ("GET", "/api/v1/users/{id}", "users", "Get user profile", False),
    ("PUT", "/api/v1/users/{id}", "users", "Update user profile", False),
    ("DELETE", "/api/v1/users/{id}", "users", "Delete user account", False),
    ("GET", "/api/v1/users/search", "users", "Search users by username/bio", False),
    ("GET", "/api/v1/users/{id}/followers", "users", "List a user's followers", False),
    ("GET", "/api/v1/users/{id}/following", "users", "List who a user follows", False),
    ("POST", "/api/v1/users/{id}/follow", "users", "Follow a user", False),
    ("POST", "/api/v1/users/{id}/unfollow", "users", "Unfollow a user", False),
    ("GET", "/api/v1/posts", "posts", "List public posts", False),
    ("POST", "/api/v1/posts", "posts", "Create a post", False),
    ("GET", "/api/v1/posts/{id}", "posts", "Get a post", False),
    ("PUT", "/api/v1/posts/{id}", "posts", "Update a post", False),
    ("DELETE", "/api/v1/posts/{id}", "posts", "Delete a post", False),
    ("POST", "/api/v1/posts/{id}/like", "posts", "Like a post", False),
    ("POST", "/api/v1/posts/{id}/unlike", "posts", "Unlike a post", False),
    ("GET", "/api/v1/posts/{id}/likes", "posts", "List who liked a post", False),
    ("GET", "/api/v1/posts/{id}/comments", "comments", "List comments on a post", False),
    ("POST", "/api/v1/posts/{id}/comments", "comments", "Comment on a post", False),
    ("DELETE", "/api/v1/comments/{id}", "comments", "Delete a comment", False),
    ("GET", "/api/v1/messages/{id}", "messages", "Get a direct message", False),
    ("POST", "/api/v1/messages", "messages", "Send a direct message", False),
    ("GET", "/api/v1/messages/conversation/{id}", "messages", "Get a conversation", False),
    ("GET", "/api/v1/messages/inbox", "messages", "Get inbox", False),
    ("GET", "/api/v1/messages/sent", "messages", "Get sent messages", False),
    ("POST", "/api/v1/upload/avatar", "upload", "Upload avatar via URL", False),
    ("GET", "/api/v1/export/profile", "upload", "Export own profile data", False),
    ("GET", "/api/v1/graphql", "graphql", "GraphQL playground", False),
    ("POST", "/api/v1/graphql", "graphql", "GraphQL query/mutation endpoint", False),
    ("POST", "/api/v1/webhook/register", "webhooks", "Register a webhook URL", False),
    ("POST", "/api/v1/webhook/test/{id}", "webhooks", "Trigger a test webhook delivery", False),
    ("GET", "/api/v1/webhook/list", "webhooks", "List registered webhooks", False),
    ("GET", "/api/v1/promotions/verification/eligibility", "promotions", "Check verified-badge eligibility", False),
    ("POST", "/api/v1/promotions/verification/apply", "promotions", "Apply for verified badge", False),
    ("POST", "/api/v1/promotions/verification/revoke/{id}", "promotions", "Revoke a verified badge", False),
    ("POST", "/api/v1/integrations/import-profile", "integrations", "Import profile from a partner API", False),
    ("GET", "/api/v1/integrations/exchange-rate", "integrations", "Get an exchange rate from a provider", False),
    ("POST", "/api/v1/otp/request", "otp", "Request a one-time verification code", False),
    ("POST", "/api/v1/otp/verify", "otp", "Verify a one-time code", False),

    # ---- VULNERABILITY: internal-only paths leaked into the public spec ----
    ("GET", "/api/v1/admin/users", "internal", "[INTERNAL] List all users with full details", True),
    ("DELETE", "/api/v1/admin/users/{id}", "internal", "[INTERNAL] Delete any user", True),
    ("GET", "/api/v1/admin/stats", "internal", "[INTERNAL] Platform statistics", True),
    ("PUT", "/api/v1/admin/users/{id}/role", "internal", "[INTERNAL] Change a user's role", True),
    ("GET", "/api/v1/debug", "internal", "[INTERNAL] Debug info - DO NOT expose (leaks JWT secret)", True),
    ("POST", "/api/v1/tools/ping", "internal", "[INTERNAL] Server-side ping tool (ops use only)", True),
    ("POST", "/api/v1/tools/dns-lookup", "internal", "[INTERNAL] Server-side DNS lookup tool (ops use only)", True),
    ("POST", "/api/v1/tools/user-lookup", "internal", "[INTERNAL] Flexible user query tool (ops use only)", True),
    ("GET", "/api/v0/users", "legacy", "[DEPRECATED v0] List all users (pre-auth system)", True),
    ("GET", "/api/v0/users/{id}", "legacy", "[DEPRECATED v0] Get a user (pre-auth system)", True),
    ("PUT", "/api/v0/users/{id}", "legacy", "[DEPRECATED v0] Update a user (pre-auth system)", True),
    ("GET", "/api/v0/export-all", "legacy", "[DEPRECATED v0] Full database export (pre-auth system)", True),
    ("GET", "/api/v1/gateway-internal/stats", "internal",
     "[INTERNAL] Infrastructure stats - requires X-Gateway-Verified header, gateway-protected", True),
]


def _build_openapi_spec():
    paths = {}
    for method, path, tag, summary, internal in _ENDPOINTS:
        openapi_path = path  # already uses {id}-style placeholders
        paths.setdefault(openapi_path, {})
        paths[openapi_path][method.lower()] = {
            "summary": summary,
            "tags": [tag],
            # VULNERABILITY: "x-internal" is set correctly on sensitive paths,
            # but nothing in this route actually filters on it before
            # returning the spec - the flag is decorative only.
            "x-internal": internal,
            "responses": {"200": {"description": "OK"}},
        }

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "SocialHack API",
            "version": "1.0.0",
            "description": "Auto-generated from the route table. "
                            "TODO: filter internal/deprecated paths before publishing externally.",
        },
        "servers": [{"url": "http://localhost:5001"}],
        "paths": paths,
    }


@docs_bp.route("/openapi.json", methods=["GET"])
def openapi_spec():
    """Serve the auto-generated OpenAPI spec.

    VULNERABILITY (API9:2023 - Improper Inventory Management): this spec is
    generated from the FULL route table, including admin, debug, internal
    "ops tooling", and deprecated v0 endpoints. Nothing filters out paths
    tagged x-internal=true before the spec is served, so anyone who finds
    this URL gets a complete, unauthenticated map of the entire attack
    surface - including endpoints that are otherwise hard to guess.
    """
    return jsonify(_build_openapi_spec()), 200


@docs_bp.route("/swagger", methods=["GET"])
def swagger_ui():
    """Minimal, self-contained API docs viewer (no external CDN required).

    Renders the same over-shared /openapi.json spec as an HTML table, with
    internal/legacy paths visually flagged (in the UI - but of course
    still fully reachable over the network).
    """
    spec = _build_openapi_spec()
    rows = []
    for path, methods in sorted(spec["paths"].items()):
        for method, info in methods.items():
            internal = info.get("x-internal")
            badge = "🔴 INTERNAL" if internal else ""
            rows.append(
                f"<tr class=\"{'internal' if internal else ''}\">"
                f"<td>{method.upper()}</td><td>{path}</td>"
                f"<td>{info['tags'][0]}</td><td>{info['summary']}</td><td>{badge}</td></tr>"
            )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>SocialHack API Docs</title>
<style>
body {{ font-family: monospace; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
tr.internal {{ background: #ffe5e5; }}
h1 {{ font-size: 1.2rem; }}
</style></head>
<body>
<h1>SocialHack API - Auto-generated Docs (source: /openapi.json)</h1>
<p>{len(rows)} endpoints found across the deployed route table.</p>
<table>
<tr><th>Method</th><th>Path</th><th>Tag</th><th>Summary</th><th></th></tr>
{''.join(rows)}
</table>
</body></html>"""
    return Response(html, mimetype="text/html")

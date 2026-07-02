"""Internal-only infrastructure endpoints, meant to be reachable only
through a trusted API Gateway.

A REAL API Gateway misconfiguration bug almost always involves TWO
different HTTP implementations disagreeing about how to parse the same
request (e.g. nginx vs. the app server, or Kong vs. the upstream) - a
single Flask process can't fully reproduce that class of bug on its own,
because there's only one HTTP parser (Werkzeug) involved. This module
SIMULATES the pattern with a simplified "fake gateway" layer (see the
before_request hook in app/__init__.py) so the two bypass techniques below
can be demonstrated end-to-end, with the simplification called out
explicitly in Stage 7.7.

VULNERABILITIES (simulated gateway misconfiguration):
1. The gateway's protected-path check is a naive EXACT STRING match
   against request.path. Since this route is registered with
   strict_slashes=False, a trailing-slash variant of the same URL still
   routes to this handler but does NOT match the gateway's exact-match
   blocklist - trivial bypass, no header needed at all.
2. A second, differently-named ALIAS route reaches the exact same
   handler. The gateway's protected-path list was never updated to
   include this alias - a very common real mistake when a team adds a
   new route/alias for an existing internal service.
3. The gateway's "trust" mechanism is just a plain HTTP header
   (X-Gateway-Verified) with a fixed expected value - there is no
   cryptographic binding (like mutual TLS) proving the request actually
   came through the real gateway. Any external client can set this
   header itself.
"""

from flask import Blueprint, jsonify, current_app

gateway_bp = Blueprint("gateway_internal", __name__)


def _infra_stats_payload():
    return {
        "warning": "INTERNAL - infrastructure details, gateway-protected in theory",
        "internal_hostnames": ["db-primary.internal", "cache-01.internal", "worker-03.internal"],
        "internal_network": "10.42.0.0/16",
        "deploy_environment": "staging-mirrors-prod",
        "flag": "FLAG{gateway_bypass_via_trailing_slash_or_alias_route}",
    }


@gateway_bp.route("/gateway-internal/stats", methods=["GET"], strict_slashes=False)
def internal_infra_stats():
    """[GATEWAY-PROTECTED] Infrastructure stats - see app/__init__.py's
    fake_gateway_layer() for the (bypassable) protection logic."""
    return jsonify(_infra_stats_payload()), 200


@gateway_bp.route("/internal/infra-stats", methods=["GET"])
def internal_infra_stats_alias():
    """[UNPROTECTED ALIAS] Same data as /gateway-internal/stats, reached
    through a path the gateway's blocklist was never updated to cover.

    VULNERABILITY: route-coverage gap. Whoever configured the gateway
    protected this specific path string, but a teammate later added this
    alias for the same underlying service and nobody updated the
    gateway's rule list.
    """
    return jsonify(_infra_stats_payload()), 200

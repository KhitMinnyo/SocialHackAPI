"""Web UI page for the /api/v1/upload/avatar endpoint (SSRF lab,
app/routes/upload.py, OWASP API7:2023 - Server-Side Request Forgery).

Same house rule as the rest of app/routes/web_*.py: this file has no
logic of its own - the page's own JavaScript (app/static/js/avatar-picker.js)
calls the existing, unmodified /api/v1/upload/avatar endpoint via
SH.apiFetch().

The page offers 5 built-in preset avatars (small PNGs under
app/static/mock-partner/avatars/) instead of a free-text "avatar URL"
field, and never prints any of those URLs as visible text or as a plain
<img src>: each thumbnail is fetched with JavaScript and rendered from an
in-memory Blob, so the address it was loaded from only shows up in the
browser's own DevTools -> Network tab - the same place any other image
request would show up. Choosing a preset still sends a real, absolute
URL to POST /api/v1/upload/avatar, so the endpoint performs the exact
same server-side fetch it always has. The SSRF vulnerability itself is
completely unchanged; this page only changes how the picker looks, not
what the API does or accepts.
"""
from flask import Blueprint, render_template

web_avatar_bp = Blueprint("web_avatar", __name__)


@web_avatar_bp.route("/app/avatar", methods=["GET"])
def avatar_page():
    return render_template("web/avatar_picker.html")

"""Web UI pages for a few low-level lab endpoints, grouped under a
"Developer" menu: the /api/v1/tools/* network tools (ping, dns-lookup)
from app/routes/misc.py, and the /api/v1/upload/document (+ the paired
/api/v1/upload/view) file upload endpoints from app/routes/upload.py.

Same house rule as the rest of app/routes/web_*.py: this file has no
logic of its own - the page's own JavaScript (app/static/js/dev-ping.js,
dev-dns-lookup.js, dev-upload.js) calls those endpoints via fetch(). The
one addition to the underlying API for this whole feature set is
GET /api/v1/upload/view in upload.py: a new route (not a change to any
existing route) added specifically so the upload page could read a file
back - it deliberately carries the same path-traversal bug as
upload_document() so the write-then-read Chapter 24 demo works
end-to-end through the browser.
"""
from flask import Blueprint, render_template

web_developer_bp = Blueprint("web_developer", __name__)


@web_developer_bp.route("/", methods=["GET"])
def developer_page():
    """Landing page linking to the tools below."""
    return render_template("web/developer.html")


@web_developer_bp.route("/ping", methods=["GET"])
def dev_ping_page():
    return render_template("web/dev_ping.html")


@web_developer_bp.route("/dns-lookup", methods=["GET"])
def dev_dns_lookup_page():
    return render_template("web/dev_dns_lookup.html")


@web_developer_bp.route("/upload", methods=["GET"])
def dev_upload_page():
    return render_template("web/dev_upload.html")

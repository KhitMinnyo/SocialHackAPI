"""Web UI page for the /api/v1/users/search endpoint (SQL Injection lab,
app/routes/users.py, OWASP-adjacent "Advanced" chapter on SQLi).

Same house rule as the rest of app/routes/web_*.py: this file has no
logic of its own - the page's own JavaScript (app/static/js/search.js)
calls the existing, unmodified /api/v1/users/search endpoint via
SH.apiFetch().

One deliberate difference from every other web_*.py page built so far:
search.js includes a client-side-only "filter" that strips characters
commonly used to break out of the vulnerable SQL string (', --, /* */,
;) before the request ever leaves the browser. That makes typing a
single quote into this page's search box completely harmless - no SQL
syntax error, no injection - while /api/v1/users/search itself is not
touched at all and stays exactly as vulnerable as it always was.

The lesson this page exists to demonstrate: a front-end filter protects
the UI you built, not the API underneath it. Anyone who calls
/api/v1/users/search directly (curl, Postman, or editing/replaying the
request in Burp) skips this page's JavaScript entirely and can still
inject - a safe-looking web app does not imply a safe API.
"""
from flask import Blueprint, render_template

web_search_bp = Blueprint("web_search", __name__)


@web_search_bp.route("/app/search", methods=["GET"])
def search_page():
    return render_template("web/search.html")

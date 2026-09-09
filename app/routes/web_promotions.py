"""Web UI page for the /api/v1/promotions/verification/* endpoints
(OWASP API6:2023 - Unrestricted Access to Sensitive Business Flows,
app/routes/promotions.py).

Same house rule as the rest of app/routes/web_*.py: this file has no
logic of its own - the page's own JavaScript (app/static/js/verification.js)
calls the existing, unmodified /api/v1/promotions/verification/eligibility
and /api/v1/promotions/verification/apply endpoints via SH.apiFetch().

Unlike web_search.py, this page has no client-side twist at all: it is a
plain front end for a business flow that is already fully automated (and
already vulnerable - no human review, no rate limit, no bot detection)
on the API side. Nothing here needs to filter or block anything, so
nothing does.
"""
from flask import Blueprint, render_template

web_promotions_bp = Blueprint("web_promotions", __name__)


@web_promotions_bp.route("/app/verification", methods=["GET"])
def verification_page():
    return render_template("web/verification.html")

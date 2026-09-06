"""Web UI pages for the /api/v1/integrations/* "partner API" endpoints
(exchange-rate, import-profile).

Same house rule as app/routes/web.py and app/routes/web_password_reset.py:
this file has NO logic of its own. It only renders page shells - the
page's own JavaScript (app/static/js/exchange-rate.js and
import-profile.js) calls the existing, unmodified endpoints in
app/routes/integrations.py via fetch(), exactly like every other page in
this UI. Nothing here is new backend behavior.
"""
from flask import Blueprint, render_template

web_integrations_bp = Blueprint("web_integrations", __name__)


@web_integrations_bp.route("/", methods=["GET"])
def integrations_page():
    """Landing page linking to the two integration demos below."""
    return render_template("web/integrations.html")


@web_integrations_bp.route("/exchange-rate", methods=["GET"])
def exchange_rate_page():
    return render_template("web/exchange_rate.html")


@web_integrations_bp.route("/import-profile", methods=["GET"])
def import_profile_page():
    return render_template("web/import_profile.html")

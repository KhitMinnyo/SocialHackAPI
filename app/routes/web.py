"""SocialHack Web UI - a thin, non-vulnerable client for the API.

IMPORTANT: This blueprint contains NO intentional vulnerabilities of its own.
Every route here does nothing more than render a Jinja2 page shell (HTML/CSS)
and pass a couple of harmless URL parameters (like a post_id or user_id) into
the template for the page's own JavaScript to use. There is no session, no
server-side auth check, and no direct database access anywhere in this file.

All real data loading and every mutation (login, register, posting, liking,
following, messaging, admin actions, ...) happens client-side: the page's
JavaScript (see app/static/js/*.js) calls the REAL, already-vulnerable JSON
API at /api/v1/* using fetch(), exactly the way a real single-page app would.

Why this design, and why it matters for the course:
- Students get a realistic "browse the app like a normal user" experience
  instead of only ever hitting the API with curl/Postman.
- Because the browser is making the real API calls, everything taught in
  Stage 2 (Burp Suite / proxying) still applies directly: point Burp at the
  browser, click around SocialHack normally, and every request you see in
  Burp's HTTP history is a real, replayable, modifiable request against the
  same vulnerable endpoints documented throughout this course.
- The UI intentionally mirrors real-world sloppiness: action buttons (edit
  post, delete comment, the "Admin" nav link, etc.) are only shown when the
  currently logged-in user "should" see them, based on client-side checks
  against locally-stored user data. But since the underlying API endpoints
  perform little-to-no server-side authorization of their own (that's the
  whole point of this course), hiding a button in the UI does NOT protect
  the underlying action - a student who intercepts a request (or edits the
  URL bar, e.g. /app/profile/<id> or /app/post/<id>) can still trigger it.
  This is a very common real-world pattern: "security by hidden button."

See Tutorial 2.5 ("SocialHack Web UI နှင့် Burp Suite ချိတ်ဆက်နည်း") for the
full walkthrough of using this UI as a pivot point into the API labs.
"""

from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    """Landing page. JS decides (client-side) whether to bounce to the feed
    or the login page, based on whether a token is already stored locally."""
    return render_template("web/index.html")


@web_bp.route("/register")
def register_page():
    return render_template("web/register.html")


@web_bp.route("/login")
def login_page():
    return render_template("web/login.html")


@web_bp.route("/feed")
def feed_page():
    return render_template("web/feed.html")


@web_bp.route("/profile/<int:user_id>")
def profile_page(user_id):
    """No ownership/existence check here on purpose - this is just a page
    shell. Whether user_id "belongs" to you, is private, or even exists at
    all is entirely determined by what GET /api/v1/users/<id> returns when
    the page's JS calls it. Try editing this number in the URL bar."""
    return render_template("web/profile.html", user_id=user_id)


@web_bp.route("/post/<int:post_id>")
def post_detail_page(post_id):
    """Same idea as profile_page: post_id is passed through untouched."""
    return render_template("web/post_detail.html", post_id=post_id)


@web_bp.route("/messages")
def messages_page():
    return render_template("web/messages.html")


@web_bp.route("/messages/conversation/<int:user_id>")
def conversation_page(user_id):
    return render_template("web/messages.html", conversation_user_id=user_id)


@web_bp.route("/admin")
def admin_page():
    """The nav bar only links here for users whose locally-stored role is
    "admin" - but the page (and the /api/v1/admin/* endpoints it calls) do
    not actually check that server-side. Navigate here directly as any
    logged-in user to see for yourself (this is Stage 5.2's BFLA lesson,
    now reachable by URL instead of only by curl)."""
    return render_template("web/admin.html")

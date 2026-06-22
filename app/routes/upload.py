"""Upload and export routes with intentional vulnerabilities."""

import os
import requests as http_requests
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import User
from app.utils import token_required

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload/avatar", methods=["POST"])
@token_required
def upload_avatar():
    """Upload avatar via URL.

    VULNERABILITY: SSRF - fetches URL server-side without validation.
    Can be used to:
    - Access internal services (localhost, 127.0.0.1)
    - Read cloud metadata (169.254.169.254)
    - Scan internal network
    - Access file:// protocol
    """
    data = request.get_json()

    if not data or not data.get("url"):
        return jsonify({"error": "URL is required. Send {\"url\": \"https://example.com/image.jpg\"}"}), 400

    url = data["url"]

    # VULNERABILITY: No URL validation - accepts any URL including internal ones
    try:
        # VULNERABILITY: Server makes request to user-supplied URL
        response = http_requests.get(url, timeout=5, allow_redirects=True)

        # Try to determine if it's an image (but accept anything)
        content_type = response.headers.get("Content-Type", "")

        # Save the response
        if response.status_code == 200:
            # For non-image responses (SSRF exploitation), return the content
            if "image" not in content_type:
                return jsonify({
                    "message": "URL fetched (not an image)",
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": len(response.content),
                    # VULNERABILITY: Returns fetched content - enables SSRF data exfiltration
                    "response_body": response.text[:5000],
                }), 200

            # Save image
            upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            filename = f"avatar_{request.current_user_id}.jpg"
            filepath = os.path.join(upload_dir, filename)

            with open(filepath, "wb") as f:
                f.write(response.content)

            # Update user profile pic
            user = User.query.get(request.current_user_id)
            if user:
                user.profile_pic = f"/uploads/{filename}"
                db.session.commit()

            return jsonify({
                "message": "Avatar uploaded successfully",
                "avatar_url": f"/uploads/{filename}",
                "source_url": url,
                "content_type": content_type,
                "size": len(response.content),
            }), 200
        else:
            return jsonify({
                "error": f"Failed to fetch URL: HTTP {response.status_code}",
                "response_body": response.text[:2000],
            }), 400

    except http_requests.exceptions.ConnectionError as e:
        # VULNERABILITY: Reveals internal network information in errors
        return jsonify({
            "error": f"Connection failed: {str(e)}",
            "url": url,
        }), 500
    except http_requests.exceptions.Timeout:
        return jsonify({
            "error": "Request timed out",
            "url": url,
        }), 504
    except Exception as e:
        return jsonify({
            "error": f"Request failed: {str(e)}",
            "url": url,
        }), 500


@upload_bp.route("/export/profile", methods=["GET"])
@token_required
def export_profile():
    """Export user profile data.

    VULNERABILITY: Excessive Data Exposure - returns ALL user data including
    password hash, internal notes, API keys, and other sensitive fields.
    """
    user = User.query.get(request.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # VULNERABILITY: Uses to_full_dict() which exposes everything
    export_data = {
        "export_type": "full_profile",
        "exported_at": __import__("datetime").datetime.now().isoformat(),
        "user_data": user.to_full_dict(),
        "posts": [p.to_dict() for p in user.posts.all()],
        "followers_count": user.followers_list.count(),
        "following_count": user.followed.count(),
        # VULNERABILITY: Exposing follower details
        "followers": [f.to_private_dict() for f in user.followers_list.all()],
        "following": [f.to_private_dict() for f in user.followed.all()],
    }

    return jsonify(export_data), 200

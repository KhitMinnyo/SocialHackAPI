"""Comment routes."""

from flask import Blueprint, request, jsonify
from app import db
from app.models import Comment, Post
from app.utils import token_required

comments_bp = Blueprint("comments", __name__)


@comments_bp.route("/posts/<int:post_id>/comments", methods=["GET"])
@token_required
def get_comments(post_id):
    """Get comments for a post."""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()

    return jsonify({
        "post_id": post_id,
        "comments_count": len(comments),
        "comments": [c.to_dict() for c in comments],
    }), 200


@comments_bp.route("/posts/<int:post_id>/comments", methods=["POST"])
@token_required
def create_comment(post_id):
    """Create a comment on a post.

    VULNERABILITY: Can comment on private posts.
    """
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # VULNERABILITY: No check if post is private
    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"error": "Content is required"}), 400

    comment = Comment(
        post_id=post_id,
        user_id=request.current_user_id,
        content=data["content"],
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "message": "Comment created",
        "comment": comment.to_dict(),
    }), 201


@comments_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@token_required
def delete_comment(comment_id):
    """Delete a comment.

    VULNERABILITY: BOLA - can delete any comment.
    """
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    # VULNERABILITY: No ownership check
    db.session.delete(comment)
    db.session.commit()

    return jsonify({"message": "Comment deleted"}), 200

"""Post routes with intentional vulnerabilities."""

from flask import Blueprint, request, jsonify
from app import db
from app.models import Post, Like, User
from app.utils import token_required

posts_bp = Blueprint("posts", __name__)


@posts_bp.route("", methods=["GET"])
@token_required
def get_posts():
    """Get all public posts.

    VULNERABILITY: No pagination limit - can dump entire database.
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)

    # VULNERABILITY: No maximum limit on per_page
    posts = Post.query.filter_by(is_public=True).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "posts": [post.to_dict() for post in posts.items],
        "total": posts.total,
        "page": posts.page,
        "pages": posts.pages,
        "per_page": per_page,
    }), 200


@posts_bp.route("/<int:post_id>", methods=["GET"])
@token_required
def get_post(post_id):
    """Get a specific post.

    VULNERABILITY: BOLA - can access private posts by ID.
    """
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # VULNERABILITY: No check if post is private and user has permission
    return jsonify({"post": post.to_dict()}), 200


@posts_bp.route("", methods=["POST"])
@token_required
def create_post():
    """Create a new post."""
    data = request.get_json()

    if not data or not data.get("content"):
        return jsonify({"error": "Content is required"}), 400

    post = Post(
        user_id=request.current_user_id,
        content=data.get("content"),
        image_url=data.get("image_url", ""),
        is_public=data.get("is_public", True),
    )

    db.session.add(post)
    db.session.commit()

    return jsonify({
        "message": "Post created successfully",
        "post": post.to_dict(),
    }), 201


@posts_bp.route("/<int:post_id>", methods=["PUT"])
@token_required
def update_post(post_id):
    """Update a post.

    VULNERABILITY: BOLA - can update any post, not just own.
    """
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # VULNERABILITY: No check if current user owns this post
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "content" in data:
        post.content = data["content"]
    if "image_url" in data:
        post.image_url = data["image_url"]
    if "is_public" in data:
        post.is_public = data["is_public"]

    db.session.commit()

    return jsonify({
        "message": "Post updated successfully",
        "post": post.to_dict(),
    }), 200


@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@token_required
def delete_post(post_id):
    """Delete a post.

    VULNERABILITY: BOLA - can delete any post, not just own.
    """
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # VULNERABILITY: No check if current user owns this post
    db.session.delete(post)
    db.session.commit()

    return jsonify({"message": "Post deleted successfully"}), 200


@posts_bp.route("/<int:post_id>/like", methods=["POST"])
@token_required
def like_post(post_id):
    """Like a post.

    VULNERABILITY: No rate limiting, no duplicate check (race condition).
    """
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # VULNERABILITY: No duplicate check - allows multiple likes from same user
    # This enables like bombing and race condition exploitation
    like = Like(post_id=post_id, user_id=request.current_user_id)
    db.session.add(like)

    post.likes_count += 1
    db.session.commit()

    return jsonify({
        "message": "Post liked",
        "likes_count": post.likes_count,
    }), 200


@posts_bp.route("/<int:post_id>/unlike", methods=["POST"])
@token_required
def unlike_post(post_id):
    """Unlike a post."""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    like = Like.query.filter_by(post_id=post_id, user_id=request.current_user_id).first()
    if not like:
        return jsonify({"error": "You haven't liked this post"}), 400

    db.session.delete(like)
    post.likes_count = max(0, post.likes_count - 1)
    db.session.commit()

    return jsonify({
        "message": "Post unliked",
        "likes_count": post.likes_count,
    }), 200


@posts_bp.route("/<int:post_id>/likes", methods=["GET"])
@token_required
def get_post_likes(post_id):
    """Get users who liked a post."""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    likes = Like.query.filter_by(post_id=post_id).all()
    users = []
    for like in likes:
        user = User.query.get(like.user_id)
        if user:
            users.append(user.to_dict())

    return jsonify({
        "post_id": post_id,
        "likes_count": len(users),
        "liked_by": users,
    }), 200

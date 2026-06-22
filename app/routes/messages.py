"""Message routes with intentional vulnerabilities."""

from flask import Blueprint, request, jsonify
from app import db
from app.models import Message, User
from app.utils import token_required

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/<int:message_id>", methods=["GET"])
@token_required
def get_message(message_id):
    """Get a specific message.

    VULNERABILITY: BOLA - can read any message by ID, not just own.
    """
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Message not found"}), 404

    # VULNERABILITY: No check if current user is sender or recipient
    return jsonify({"message": message.to_dict()}), 200


@messages_bp.route("", methods=["POST"])
@token_required
def send_message():
    """Send a direct message.

    VULNERABILITY: No check on recipient - can message anyone including themselves.
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    recipient_id = data.get("recipient_id")
    content = data.get("content")

    if not recipient_id or not content:
        return jsonify({"error": "recipient_id and content are required"}), 400

    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({"error": "Recipient not found"}), 404

    # VULNERABILITY: No privacy check, no blocking, no rate limit
    message = Message(
        sender_id=request.current_user_id,
        recipient_id=recipient_id,
        content=content,
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({
        "message_status": "Message sent",
        "message": message.to_dict(),
    }), 201


@messages_bp.route("/conversation/<int:user_id>", methods=["GET"])
@token_required
def get_conversation(user_id):
    """Get conversation with a user.

    VULNERABILITY: BOLA - by manipulating user_id, can potentially see conversations.
    """
    other_user = User.query.get(user_id)
    if not other_user:
        return jsonify({"error": "User not found"}), 404

    current_user_id = request.current_user_id

    # Get messages between current user and other user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user_id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == current_user_id),
        )
    ).order_by(Message.created_at.asc()).all()

    return jsonify({
        "conversation_with": other_user.username,
        "messages_count": len(messages),
        "messages": [m.to_dict() for m in messages],
    }), 200


@messages_bp.route("/inbox", methods=["GET"])
@token_required
def get_inbox():
    """Get all received messages."""
    messages = Message.query.filter_by(
        recipient_id=request.current_user_id
    ).order_by(Message.created_at.desc()).all()

    return jsonify({
        "inbox_count": len(messages),
        "messages": [m.to_dict() for m in messages],
    }), 200


@messages_bp.route("/sent", methods=["GET"])
@token_required
def get_sent():
    """Get all sent messages."""
    messages = Message.query.filter_by(
        sender_id=request.current_user_id
    ).order_by(Message.created_at.desc()).all()

    return jsonify({
        "sent_count": len(messages),
        "messages": [m.to_dict() for m in messages],
    }), 200

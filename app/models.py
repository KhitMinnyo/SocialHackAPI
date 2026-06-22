"""Database models for SocialHack API."""

from datetime import datetime, timezone
from app import db


# Many-to-many relationship for followers
followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("created_at", db.DateTime, default=lambda: datetime.now(timezone.utc)),
)


class User(db.Model):
    """User model with intentionally exposed fields."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, default="")
    profile_pic = db.Column(db.String(255), default="")
    # VULNERABILITY: Role field that can be mass-assigned
    role = db.Column(db.String(20), default="user")  # user, admin, moderator
    is_verified = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)
    # Internal fields that should not be exposed
    reset_token = db.Column(db.String(255), nullable=True)
    api_key = db.Column(db.String(64), nullable=True)
    internal_notes = db.Column(db.Text, default="")
    login_count = db.Column(db.Integer, default=0)
    last_login_ip = db.Column(db.String(45), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    posts = db.relationship("Post", backref="author", lazy="dynamic", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="author", lazy="dynamic", cascade="all, delete-orphan")
    sent_messages = db.relationship("Message", foreign_keys="Message.sender_id", backref="sender", lazy="dynamic")
    received_messages = db.relationship("Message", foreign_keys="Message.recipient_id", backref="recipient", lazy="dynamic")

    # Followers relationship
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers_list", lazy="dynamic"),
        lazy="dynamic",
    )

    def to_dict(self):
        """Public representation."""
        return {
            "id": self.id,
            "username": self.username,
            "bio": self.bio,
            "profile_pic": self.profile_pic,
            "is_verified": self.is_verified,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_full_dict(self):
        """VULNERABILITY: Excessive data exposure - returns everything including sensitive fields."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "bio": self.bio,
            "profile_pic": self.profile_pic,
            "role": self.role,
            "is_verified": self.is_verified,
            "is_private": self.is_private,
            "reset_token": self.reset_token,
            "api_key": self.api_key,
            "internal_notes": self.internal_notes,
            "login_count": self.login_count,
            "last_login_ip": self.last_login_ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_private_dict(self):
        """Returns user data with some sensitive info (used in BOLA scenarios)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "bio": self.bio,
            "profile_pic": self.profile_pic,
            "role": self.role,
            "is_verified": self.is_verified,
            "is_private": self.is_private,
            "login_count": self.login_count,
            "last_login_ip": self.last_login_ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Post(db.Model):
    """Post model."""

    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), default="")
    likes_count = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    comments = db.relationship("Comment", backref="post", lazy="dynamic", cascade="all, delete-orphan")
    likes = db.relationship("Like", backref="post", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "author": self.author.username if self.author else None,
            "content": self.content,
            "image_url": self.image_url,
            "likes_count": self.likes_count,
            "is_public": self.is_public,
            "comments_count": self.comments.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Comment(db.Model):
    """Comment model."""

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "author": self.author.username if self.author else None,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Like(db.Model):
    """Like model."""

    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Unique constraint should exist but is intentionally missing for race condition exploitation
    # __table_args__ = (db.UniqueConstraint('post_id', 'user_id'),)

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Message(db.Model):
    """Direct message model."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender": self.sender.username if self.sender else None,
            "recipient_id": self.recipient_id,
            "recipient": self.recipient.username if self.recipient else None,
            "content": self.content,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

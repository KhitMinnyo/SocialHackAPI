"""Seed the database with sample data for labs."""

from app import db
from app.models import User, Post, Comment, Message, Like
from app.utils import hash_password
from datetime import datetime, timezone


def seed_database():
    """Populate database with test data."""

    # Clear existing data
    Like.query.delete()
    Comment.query.delete()
    Message.query.delete()
    Post.query.delete()
    User.query.delete()
    db.session.commit()

    # ========== USERS ==========
    alice = User(
        username="alice",
        email="alice@socialhack.local",
        password_hash=hash_password("password123"),
        bio="Photography enthusiast 📸 | Coffee lover ☕",
        profile_pic="/uploads/alice.jpg",
        role="user",
        is_verified=True,
        is_private=False,
        api_key="ak_alice_7f3d9a2b1c4e5f6g",
        internal_notes="Regular user, joined during beta",
        login_count=42,
        last_login_ip="192.168.1.100",
    )

    bob = User(
        username="bob",
        email="bob@socialhack.local",
        password_hash=hash_password("password123"),
        bio="Software developer | Open source contributor",
        profile_pic="/uploads/bob.jpg",
        role="user",
        is_verified=True,
        is_private=False,
        api_key="ak_bob_8h4e0b3c2d5f6g7h",
        internal_notes="Power user, reports bugs frequently",
        login_count=128,
        last_login_ip="10.0.0.55",
    )

    charlie = User(
        username="charlie",
        email="charlie_secret@socialhack.local",
        password_hash=hash_password("password123"),
        bio="Private account - close friends only 🔒",
        profile_pic="/uploads/charlie.jpg",
        role="user",
        is_verified=False,
        is_private=True,
        api_key="ak_charlie_9i5f1c4d3e6g7h8i",
        internal_notes="Has requested account deletion - pending review. SSN: 123-45-6789",
        login_count=15,
        last_login_ip="172.16.0.33",
    )

    admin_user = User(
        username="admin",
        email="admin@socialhack.local",
        password_hash=hash_password("admin123"),
        bio="Platform Administrator",
        profile_pic="/uploads/admin.jpg",
        role="admin",
        is_verified=True,
        is_private=False,
        api_key="ak_admin_MASTER_KEY_x9z8y7",
        internal_notes="Super admin - has access to all systems. AWS key: AKIA1234567890ABCDEF",
        login_count=500,
        last_login_ip="10.0.0.1",
    )

    diana = User(
        username="diana",
        email="diana@socialhack.local",
        password_hash=hash_password("diana2024!"),
        bio="Travel blogger ✈️ | Food critic 🍕",
        profile_pic="/uploads/diana.jpg",
        role="moderator",
        is_verified=True,
        is_private=False,
        api_key="ak_diana_mod_key_abc123",
        internal_notes="Moderator since 2024. Salary: $75,000",
        login_count=89,
        last_login_ip="192.168.2.200",
    )

    db.session.add_all([alice, bob, charlie, admin_user, diana])
    db.session.commit()

    # ========== FOLLOW RELATIONSHIPS ==========
    alice.followed.append(bob)
    alice.followed.append(diana)
    bob.followed.append(alice)
    bob.followed.append(charlie)
    diana.followed.append(alice)
    diana.followed.append(bob)
    db.session.commit()

    # ========== POSTS ==========
    posts = [
        Post(
            user_id=alice.id,
            content="Just captured the most amazing sunset! 🌅 #photography #nature",
            image_url="/uploads/sunset.jpg",
            likes_count=15,
            is_public=True,
        ),
        Post(
            user_id=alice.id,
            content="My secret coffee recipe that nobody knows about... ☕🤫",
            likes_count=3,
            is_public=False,  # Private post
        ),
        Post(
            user_id=bob.id,
            content="Just deployed my new open source project! Check it out 🚀 #coding #opensource",
            image_url="/uploads/code.jpg",
            likes_count=25,
            is_public=True,
        ),
        Post(
            user_id=bob.id,
            content="Found a critical vulnerability in a popular framework. Reporting to maintainers first. Details coming soon...",
            likes_count=50,
            is_public=True,
        ),
        Post(
            user_id=charlie.id,
            content="Private thoughts: I think the company is going bankrupt. The financials look terrible. Don't tell anyone! 💰📉",
            likes_count=1,
            is_public=False,  # Private post with sensitive info
        ),
        Post(
            user_id=charlie.id,
            content="Meeting notes: Budget review - Q4 losses of $2.3M. Layoffs planned for January.",
            likes_count=0,
            is_public=False,  # Private post with sensitive business info
        ),
        Post(
            user_id=diana.id,
            content="Best ramen spot in Tokyo! 🍜 The broth is incredible! #foodie #tokyo #travel",
            image_url="/uploads/ramen.jpg",
            likes_count=42,
            is_public=True,
        ),
        Post(
            user_id=admin_user.id,
            content="System maintenance scheduled for this weekend. API might be slow.",
            likes_count=5,
            is_public=True,
        ),
        Post(
            user_id=admin_user.id,
            content="INTERNAL: Server credentials - db_password: Sup3rS3cret! AWS access key rotated.",
            likes_count=0,
            is_public=False,  # Admin private post with credentials
        ),
    ]

    db.session.add_all(posts)
    db.session.commit()

    # ========== COMMENTS ==========
    comments = [
        Comment(post_id=1, user_id=bob.id, content="Stunning photo! What camera do you use?"),
        Comment(post_id=1, user_id=diana.id, content="Beautiful! Where was this taken? 😍"),
        Comment(post_id=3, user_id=alice.id, content="Congrats Bob! Will definitely check it out!"),
        Comment(post_id=3, user_id=diana.id, content="Amazing work! 🎉"),
        Comment(post_id=4, user_id=alice.id, content="Responsible disclosure FTW! 👏"),
        Comment(post_id=7, user_id=alice.id, content="I need to visit this place! Added to my bucket list."),
        Comment(post_id=7, user_id=bob.id, content="Was there last year, can confirm it's amazing!"),
    ]

    db.session.add_all(comments)
    db.session.commit()

    # ========== MESSAGES ==========
    messages = [
        Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            content="Hey Bob! Want to collaborate on a photography project?",
        ),
        Message(
            sender_id=bob.id,
            recipient_id=alice.id,
            content="Sure! That sounds awesome. What did you have in mind?",
        ),
        Message(
            sender_id=alice.id,
            recipient_id=bob.id,
            content="I was thinking we could do a photo series of urban architecture.",
        ),
        Message(
            sender_id=charlie.id,
            recipient_id=admin_user.id,
            content="Hey admin, please delete my account. My SSN was leaked in my notes. This is urgent!",
        ),
        Message(
            sender_id=admin_user.id,
            recipient_id=charlie.id,
            content="Hi Charlie, I'll process your request. For verification, what's the email on your account?",
        ),
        Message(
            sender_id=diana.id,
            recipient_id=alice.id,
            content="Alice! Your photos are amazing. Would you like to guest post on my travel blog?",
        ),
        Message(
            sender_id=alice.id,
            recipient_id=diana.id,
            content="Wow, I'd love to! Let me DM you some of my best shots from my recent trip.",
        ),
        Message(
            sender_id=bob.id,
            recipient_id=admin_user.id,
            content="Admin - found a bug: the search endpoint seems to be passing user input directly to SQL. Might want to check that.",
        ),
        Message(
            sender_id=admin_user.id,
            recipient_id=bob.id,
            content="Thanks for the report Bob. We'll look into it. Here's a temp admin password for testing: TempAdmin@2024",
        ),
    ]

    db.session.add_all(messages)
    db.session.commit()

    # ========== LIKES ==========
    like_pairs = [
        (1, bob.id), (1, diana.id), (1, charlie.id),
        (3, alice.id), (3, diana.id), (3, charlie.id),
        (4, alice.id), (4, diana.id),
        (7, alice.id), (7, bob.id),
    ]

    for post_id, user_id in like_pairs:
        like = Like(post_id=post_id, user_id=user_id)
        db.session.add(like)

    db.session.commit()

    print("[+] Database seeded successfully!")
    print(f"    Users: {User.query.count()}")
    print(f"    Posts: {Post.query.count()}")
    print(f"    Comments: {Comment.query.count()}")
    print(f"    Messages: {Message.query.count()}")
    print(f"    Likes: {Like.query.count()}")
    print()
    print("[*] Test Credentials:")
    print("    alice    / password123  (user)")
    print("    bob      / password123  (user)")
    print("    charlie  / password123  (user, private)")
    print("    admin    / admin123     (admin)")
    print("    diana    / diana2024!   (moderator)")

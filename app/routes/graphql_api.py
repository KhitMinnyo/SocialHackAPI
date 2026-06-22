"""Vulnerable GraphQL API endpoint.

VULNERABILITIES:
- Introspection enabled (exposes full schema)
- No query depth limiting (nested query attacks)
- No rate limiting on queries
- Excessive data exposure (returns sensitive fields)
- No authorization checks on certain fields
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Post, Comment, Message
from app.utils import token_required

graphql_bp = Blueprint("graphql", __name__)


def resolve_type(type_info):
    """Resolve GraphQL type from schema."""
    if isinstance(type_info, dict):
        return type_info
    return {"name": type_info}


# Manual GraphQL implementation (no external dependency needed)
# This simulates a vulnerable GraphQL endpoint

SCHEMA = {
    "types": {
        "User": {
            "fields": {
                "id": "Int",
                "username": "String",
                "email": "String",
                "bio": "String",
                "role": "String",
                "is_verified": "Boolean",
                "is_private": "Boolean",
                "password_hash": "String",  # VULNERABILITY: Exposed in schema
                "api_key": "String",  # VULNERABILITY: Exposed in schema
                "internal_notes": "String",  # VULNERABILITY: Exposed in schema
                "login_count": "Int",
                "last_login_ip": "String",
                "posts": "[Post]",
                "followers_count": "Int",
            }
        },
        "Post": {
            "fields": {
                "id": "Int",
                "content": "String",
                "author": "User",
                "likes_count": "Int",
                "is_public": "Boolean",
                "comments": "[Comment]",
                "created_at": "String",
            }
        },
        "Comment": {
            "fields": {
                "id": "Int",
                "content": "String",
                "author": "User",
                "post_id": "Int",
                "created_at": "String",
            }
        },
        "Message": {
            "fields": {
                "id": "Int",
                "content": "String",
                "sender": "User",
                "recipient": "User",
                "is_read": "Boolean",
                "created_at": "String",
            }
        },
    },
    "queries": {
        "users": {"type": "[User]", "args": {"limit": "Int", "role": "String"}},
        "user": {"type": "User", "args": {"id": "Int", "username": "String"}},
        "posts": {"type": "[Post]", "args": {"limit": "Int", "user_id": "Int"}},
        "post": {"type": "Post", "args": {"id": "Int"}},
        "messages": {"type": "[Message]", "args": {"user_id": "Int"}},
        "search": {"type": "[User]", "args": {"query": "String"}},
    },
    "mutations": {
        "createPost": {"type": "Post", "args": {"content": "String", "is_public": "Boolean"}},
        "updateUserRole": {"type": "User", "args": {"user_id": "Int", "role": "String"}},
        "deleteUser": {"type": "String", "args": {"user_id": "Int"}},
    },
}


def parse_simple_graphql(query_str):
    """Very simple GraphQL parser for common queries.

    Supports:
    - { __schema { types { name fields { name type } } } }
    - query { users { id username email } }
    - query { user(id: 1) { id username } }
    - mutation { updateUserRole(user_id: 1, role: "admin") { id role } }
    """
    query_str = query_str.strip()

    result = {
        "operation": "query",
        "name": None,
        "args": {},
        "fields": [],
    }

    # Detect introspection
    if "__schema" in query_str or "__type" in query_str:
        result["name"] = "__schema"
        return result

    # Detect mutation
    if query_str.startswith("mutation"):
        result["operation"] = "mutation"
        query_str = query_str[len("mutation"):].strip()

    # Remove query keyword
    if query_str.startswith("query"):
        query_str = query_str[len("query"):].strip()

    # Remove outer braces
    query_str = query_str.strip("{} \n\t")

    # Find the query name (first word)
    parts = query_str.split("(", 1)
    if len(parts) == 1:
        parts = query_str.split("{", 1)
        result["name"] = parts[0].strip()
    else:
        result["name"] = parts[0].strip()
        # Parse args
        args_str = parts[1].split(")", 1)[0]
        for arg in args_str.split(","):
            if ":" in arg:
                key, value = arg.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        if value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                result["args"][key] = value

    # Parse fields (simple extraction between last { and })
    if "{" in query_str:
        fields_str = query_str.split("{", 1)[1].rsplit("}", 1)[0]
        # Handle nested fields simply
        result["fields"] = [f.strip().split("{")[0].strip() for f in fields_str.split() if f.strip() and f.strip() not in "{}"]
    else:
        result["fields"] = ["id"]

    return result


def resolve_user(user, fields):
    """Resolve user fields."""
    data = {}
    for field in fields:
        if field == "id":
            data["id"] = user.id
        elif field == "username":
            data["username"] = user.username
        elif field == "email":
            data["email"] = user.email
        elif field == "bio":
            data["bio"] = user.bio
        elif field == "role":
            data["role"] = user.role
        elif field == "is_verified":
            data["is_verified"] = user.is_verified
        elif field == "is_private":
            data["is_private"] = user.is_private
        elif field == "password_hash":
            # VULNERABILITY: Exposes password hash via GraphQL
            data["password_hash"] = user.password_hash
        elif field == "api_key":
            # VULNERABILITY: Exposes API key
            data["api_key"] = user.api_key
        elif field == "internal_notes":
            # VULNERABILITY: Exposes internal notes
            data["internal_notes"] = user.internal_notes
        elif field == "login_count":
            data["login_count"] = user.login_count
        elif field == "last_login_ip":
            data["last_login_ip"] = user.last_login_ip
        elif field == "posts":
            data["posts"] = [{"id": p.id, "content": p.content} for p in user.posts.all()]
        elif field == "followers_count":
            data["followers_count"] = user.followers_list.count()
    return data


def resolve_post(post, fields):
    """Resolve post fields."""
    data = {}
    for field in fields:
        if field == "id":
            data["id"] = post.id
        elif field == "content":
            data["content"] = post.content
        elif field == "author":
            data["author"] = {"id": post.author.id, "username": post.author.username} if post.author else None
        elif field == "likes_count":
            data["likes_count"] = post.likes_count
        elif field == "is_public":
            data["is_public"] = post.is_public
        elif field == "comments":
            data["comments"] = [{"id": c.id, "content": c.content, "author": c.author.username if c.author else None} for c in post.comments.all()]
        elif field == "created_at":
            data["created_at"] = post.created_at.isoformat() if post.created_at else None
    return data


@graphql_bp.route("/graphql", methods=["POST", "GET"])
@token_required
def graphql_endpoint():
    """GraphQL endpoint.

    VULNERABILITIES:
    - Introspection enabled: exposes full schema including sensitive fields
    - No query depth limit: allows deeply nested queries
    - No authorization: any user can query any data
    - Sensitive fields exposed: password_hash, api_key, internal_notes
    - Mutations without proper auth: any user can updateUserRole, deleteUser
    """
    if request.method == "GET":
        # GraphQL Playground / Schema info
        return jsonify({
            "message": "SocialHack GraphQL API",
            "endpoint": "/api/v1/graphql",
            "method": "POST",
            "example_queries": {
                "introspection": '{ __schema { types { name fields { name type } } } }',
                "all_users": '{ users { id username email role password_hash api_key } }',
                "single_user": '{ user(id: 1) { id username email role internal_notes } }',
                "all_posts": '{ posts { id content author likes_count is_public } }',
                "messages": '{ messages(user_id: 1) { id content sender recipient } }',
                "mutation_role": 'mutation { updateUserRole(user_id: 1, role: "admin") { id username role } }',
            },
        }), 200

    data = request.get_json()
    if not data or not data.get("query"):
        return jsonify({"errors": [{"message": "Query is required"}]}), 400

    query_str = data["query"]
    variables = data.get("variables", {})

    try:
        parsed = parse_simple_graphql(query_str)

        # VULNERABILITY: Full introspection
        if parsed["name"] == "__schema":
            return jsonify({
                "data": {
                    "__schema": {
                        "types": [
                            {
                                "name": type_name,
                                "fields": [
                                    {"name": fname, "type": ftype}
                                    for fname, ftype in type_def["fields"].items()
                                ],
                            }
                            for type_name, type_def in SCHEMA["types"].items()
                        ],
                        "queryType": {"name": "Query"},
                        "mutationType": {"name": "Mutation"},
                        "queries": SCHEMA["queries"],
                        "mutations": SCHEMA["mutations"],
                    }
                }
            }), 200

        fields = parsed["fields"] if parsed["fields"] else ["id", "username"]

        # Handle queries
        if parsed["operation"] == "query":
            if parsed["name"] == "users":
                limit = parsed["args"].get("limit", 100)
                role = parsed["args"].get("role")
                query = User.query
                if role:
                    query = query.filter_by(role=role)
                users = query.limit(limit).all()
                # VULNERABILITY: No auth check, returns all data including private
                return jsonify({"data": {"users": [resolve_user(u, fields) for u in users]}}), 200

            elif parsed["name"] == "user":
                user_id = parsed["args"].get("id")
                username = parsed["args"].get("username")
                if user_id:
                    user = User.query.get(user_id)
                elif username:
                    user = User.query.filter_by(username=username).first()
                else:
                    return jsonify({"errors": [{"message": "id or username required"}]}), 400

                if not user:
                    return jsonify({"errors": [{"message": "User not found"}]}), 404

                return jsonify({"data": {"user": resolve_user(user, fields)}}), 200

            elif parsed["name"] == "posts":
                limit = parsed["args"].get("limit", 100)
                user_id = parsed["args"].get("user_id")
                query = Post.query
                if user_id:
                    query = query.filter_by(user_id=user_id)
                # VULNERABILITY: No privacy check - returns private posts
                posts = query.limit(limit).all()
                return jsonify({"data": {"posts": [resolve_post(p, fields) for p in posts]}}), 200

            elif parsed["name"] == "post":
                post_id = parsed["args"].get("id")
                post = Post.query.get(post_id)
                if not post:
                    return jsonify({"errors": [{"message": "Post not found"}]}), 404
                return jsonify({"data": {"post": resolve_post(post, fields)}}), 200

            elif parsed["name"] == "messages":
                # VULNERABILITY: Can read any user's messages
                user_id = parsed["args"].get("user_id", request.current_user_id)
                messages = Message.query.filter(
                    db.or_(Message.sender_id == user_id, Message.recipient_id == user_id)
                ).all()
                result = []
                for m in messages:
                    msg_data = {"id": m.id, "content": m.content, "is_read": m.is_read}
                    if "sender" in fields:
                        msg_data["sender"] = m.sender.username if m.sender else None
                    if "recipient" in fields:
                        msg_data["recipient"] = m.recipient.username if m.recipient else None
                    if "created_at" in fields:
                        msg_data["created_at"] = m.created_at.isoformat() if m.created_at else None
                    result.append(msg_data)
                return jsonify({"data": {"messages": result}}), 200

            elif parsed["name"] == "search":
                q = parsed["args"].get("query", "")
                users = User.query.filter(User.username.like(f"%{q}%")).all()
                return jsonify({"data": {"search": [resolve_user(u, fields) for u in users]}}), 200

            else:
                return jsonify({"errors": [{"message": f"Unknown query: {parsed['name']}"}]}), 400

        # Handle mutations
        elif parsed["operation"] == "mutation":
            if parsed["name"] == "updateUserRole":
                # VULNERABILITY: No admin check - any user can change roles
                user_id = parsed["args"].get("user_id")
                new_role = parsed["args"].get("role")
                user = User.query.get(user_id)
                if not user:
                    return jsonify({"errors": [{"message": "User not found"}]}), 404
                user.role = new_role
                db.session.commit()
                return jsonify({"data": {"updateUserRole": resolve_user(user, fields)}}), 200

            elif parsed["name"] == "deleteUser":
                # VULNERABILITY: No admin check
                user_id = parsed["args"].get("user_id")
                user = User.query.get(user_id)
                if not user:
                    return jsonify({"errors": [{"message": "User not found"}]}), 404
                username = user.username
                db.session.delete(user)
                db.session.commit()
                return jsonify({"data": {"deleteUser": f"User {username} deleted"}}), 200

            elif parsed["name"] == "createPost":
                content = parsed["args"].get("content", "")
                is_public = parsed["args"].get("is_public", True)
                post = Post(user_id=request.current_user_id, content=content, is_public=is_public)
                db.session.add(post)
                db.session.commit()
                return jsonify({"data": {"createPost": resolve_post(post, fields)}}), 200

            else:
                return jsonify({"errors": [{"message": f"Unknown mutation: {parsed['name']}"}]}), 400

    except Exception as e:
        # VULNERABILITY: Verbose error messages
        return jsonify({
            "errors": [{"message": f"GraphQL execution error: {str(e)}"}],
            "query": query_str,
        }), 500

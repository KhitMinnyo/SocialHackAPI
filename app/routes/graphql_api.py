"""Vulnerable GraphQL API endpoint.

VULNERABILITIES:
- Introspection enabled (exposes full schema)
- No query depth limiting (nested query attacks)
- No rate limiting on queries
- Excessive data exposure (returns sensitive fields)
- No authorization checks on certain fields
- Alias-based batching within a single query document (Stage 7.5)
- Transport-level batch arrays with no size limit (Stage 7.5)
- Persisted-query allowlist that can be bypassed (Stage 7.5)
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


# ===========================================================================
# PERSISTED QUERIES (Stage 7.5)
# ===========================================================================
# In a real "persisted queries" setup, a production API is locked down to
# only accept a pre-approved allowlist of query hashes - arbitrary `query`
# text is supposed to be rejected outright once this mode is enabled. This
# is a genuine security control some teams rely on.
PERSISTED_QUERIES = {
    # sha256("{ posts { id content } }") - a pretend pre-approved query
    "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3": '{ posts { id content } }',
}


def _extract_persisted_hash(data):
    if not isinstance(data, dict):
        return None
    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        return None
    pq = extensions.get("persistedQuery")
    if not isinstance(pq, dict):
        return None
    return pq.get("sha256Hash")


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


# ===========================================================================
# ALIAS-AWARE MULTI-SELECTION PARSER (Stage 7.5)
# ===========================================================================
# Real GraphQL lets a single query document contain MULTIPLE aliased
# selections of the same field, e.g.:
#     { a: user(id: 1) { username }  b: user(id: 2) { username } }
# This is legitimate GraphQL syntax (used to fetch several resources in one
# round trip) - but with no per-alias limit, it also lets a caller pack an
# unbounded number of logical operations into a single HTTP request,
# bypassing any rate limiter that counts "requests" rather than
# "operations" (e.g. it could be used to brute-force many user IDs, or
# many login-style checks, in one call).
#
# This splitter only handles TOP-LEVEL selections (it does not attempt a
# full GraphQL grammar) but is balanced-brace aware, so nested field
# selections like `posts { id content }` don't confuse it.

def _split_top_level_selections(inner):
    """Split a selection-set body into (alias, name, args_str, fields_str)
    tuples, honoring brace nesting. Returns [] if it can't confidently
    parse anything (caller should fall back to the legacy parser)."""
    import re

    selection_start_re = re.compile(r'(?:(\w+)\s*:\s*)?(\w+)\s*(\([^)]*\))?')

    selections = []
    i = 0
    n = len(inner)
    while i < n:
        while i < n and inner[i].isspace():
            i += 1
        if i >= n:
            break

        m = selection_start_re.match(inner, i)
        if not m or not m.group(2):
            break  # can't confidently parse further

        alias, name, args_paren = m.group(1), m.group(2), m.group(3)
        args_str = args_paren[1:-1] if args_paren else None
        i = m.end()

        while i < n and inner[i].isspace():
            i += 1

        fields_str = None
        if i < n and inner[i] == "{":
            depth = 0
            j = i
            while j < n:
                if inner[j] == "{":
                    depth += 1
                elif inner[j] == "}":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                j += 1
            fields_str = inner[i + 1:j - 1]
            i = j
        else:
            # No trailing {} - this doesn't look like a valid selection
            # boundary; stop rather than risk mis-parsing.
            selections.append((alias, name, args_str, fields_str))
            break

        selections.append((alias, name, args_str, fields_str))

    return selections


def _parse_args_string(args_str):
    args = {}
    if not args_str:
        return args
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
            args[key] = value
    return args


def _flatten_fields(fields_str):
    if not fields_str:
        return ["id"]
    cleaned = fields_str.replace("{", " ").replace("}", " ")
    fields = [f.strip() for f in cleaned.split() if f.strip()]
    return fields if fields else ["id"]


def parse_multi_selection_document(query_str):
    """Try to parse `query_str` as a multi-selection (aliased) document.

    Returns (operation_type, [ {alias, name, args, fields}, ... ]) if 2+
    top-level selections were found, otherwise returns (None, []) so the
    caller falls back to the original single-operation parser (preserving
    100% backward compatibility with every existing lesson/lab).
    """
    body = query_str.strip()

    operation_type = "query"
    if body.startswith("mutation"):
        operation_type = "mutation"
        body = body[len("mutation"):].strip()
    elif body.startswith("query"):
        body = body[len("query"):].strip()

    if not body.startswith("{"):
        brace_idx = body.find("{")
        if brace_idx == -1:
            return None, []
        body = body[brace_idx:]

    inner = body.strip()
    if inner.startswith("{"):
        inner = inner[1:]
    if inner.endswith("}"):
        inner = inner[:-1]

    raw_selections = _split_top_level_selections(inner)
    if len(raw_selections) < 2:
        return None, []

    operations = []
    for alias, name, args_str, fields_str in raw_selections:
        operations.append({
            "alias": alias or name,
            "name": name,
            "args": _parse_args_string(args_str),
            "fields": _flatten_fields(fields_str),
        })

    return operation_type, operations


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


def _resolve_single_selection(operation_type, name, args, fields, current_user_id):
    """Resolve ONE named operation (query or mutation) and return its
    result value (or an error dict). Used by both the alias-multi-selection
    path and the batch path in graphql_endpoint(). Mirrors the exact same
    resolution rules as the legacy single-operation branch below - kept as
    a separate function (rather than shared) so the original code path is
    never touched, minimizing regression risk for existing lessons.
    """
    try:
        if operation_type == "query":
            if name == "users":
                limit = args.get("limit", 100)
                role = args.get("role")
                query = User.query
                if role:
                    query = query.filter_by(role=role)
                users = query.limit(limit).all()
                return {"value": [resolve_user(u, fields) for u in users]}, None

            elif name == "user":
                user_id = args.get("id")
                username = args.get("username")
                if user_id:
                    user = User.query.get(user_id)
                elif username:
                    user = User.query.filter_by(username=username).first()
                else:
                    return None, "id or username required"
                if not user:
                    return None, "User not found"
                return {"value": resolve_user(user, fields)}, None

            elif name == "posts":
                limit = args.get("limit", 100)
                user_id = args.get("user_id")
                query = Post.query
                if user_id:
                    query = query.filter_by(user_id=user_id)
                posts = query.limit(limit).all()
                return {"value": [resolve_post(p, fields) for p in posts]}, None

            elif name == "post":
                post_id = args.get("id")
                post = Post.query.get(post_id)
                if not post:
                    return None, "Post not found"
                return {"value": resolve_post(post, fields)}, None

            elif name == "messages":
                user_id = args.get("user_id", current_user_id)
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
                    result.append(msg_data)
                return {"value": result}, None

            elif name == "search":
                q = args.get("query", "")
                users = User.query.filter(User.username.like(f"%{q}%")).all()
                return {"value": [resolve_user(u, fields) for u in users]}, None

            else:
                return None, f"Unknown query: {name}"

        elif operation_type == "mutation":
            if name == "updateUserRole":
                user_id = args.get("user_id")
                new_role = args.get("role")
                user = User.query.get(user_id)
                if not user:
                    return None, "User not found"
                user.role = new_role
                db.session.commit()
                return {"value": resolve_user(user, fields)}, None

            elif name == "deleteUser":
                user_id = args.get("user_id")
                user = User.query.get(user_id)
                if not user:
                    return None, "User not found"
                username = user.username
                db.session.delete(user)
                db.session.commit()
                return {"value": f"User {username} deleted"}, None

            elif name == "createPost":
                content = args.get("content", "")
                is_public = args.get("is_public", True)
                post = Post(user_id=current_user_id, content=content, is_public=is_public)
                db.session.add(post)
                db.session.commit()
                return {"value": resolve_post(post, fields)}, None

            else:
                return None, f"Unknown mutation: {name}"

        return None, "Unsupported operation type"
    except Exception as e:
        return None, f"GraphQL execution error: {str(e)}"


def _process_single_document(data, current_user_id):
    """Process one {query, variables, extensions} document and return a
    JSON-serializable response dict (the same shape a single POST /graphql
    call has always returned). Used directly for normal requests, and once
    per item for batch-array requests (Stage 7.5)."""
    if not isinstance(data, dict):
        return {"errors": [{"message": "Each batch item must be an object with a 'query' field"}]}

    query_str = data.get("query")
    persisted_hash = _extract_persisted_hash(data)

    if not query_str and persisted_hash:
        # Strict persisted-query mode: only the allowlisted text may run.
        query_str = PERSISTED_QUERIES.get(persisted_hash)
        if not query_str:
            return {"errors": [{"message": "PersistedQueryNotFound"}]}
    elif query_str and persisted_hash:
        # VULNERABILITY (Persisted Query Bypass): a raw `query` was supplied
        # ALONGSIDE a persistedQuery hash. A properly enforced "persisted
        # queries only" mode should reject this combination outright and
        # refuse to execute arbitrary query text. This implementation does
        # not - it just falls through and executes `query_str` as normal,
        # meaning the persisted-query allowlist provides no real protection
        # whatsoever once a caller learns it can just add its own `query`.
        pass

    if not query_str:
        return {"errors": [{"message": "Query is required"}]}

    try:
        # Try the new alias/multi-selection parser first. It only "engages"
        # when it finds 2+ top-level selections; anything it can't
        # confidently parse (including every existing single-query example
        # from earlier lessons) falls through to the original parser below,
        # completely unchanged.
        multi_op_type, operations = parse_multi_selection_document(query_str)

        if multi_op_type and len(operations) >= 2:
            result_data = {}
            errors = []
            for op in operations:
                value_wrapper, err = _resolve_single_selection(
                    multi_op_type, op["name"], op["args"], op["fields"], current_user_id
                )
                if err:
                    errors.append({"message": err, "path": [op["alias"]]})
                else:
                    result_data[op["alias"]] = value_wrapper["value"]
            response = {"data": result_data}
            if errors:
                response["errors"] = errors
            return response

        # ── Original single-operation parsing path (UNCHANGED) ──
        parsed = parse_simple_graphql(query_str)

        # VULNERABILITY: Full introspection
        if parsed["name"] == "__schema":
            return {
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
            }

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
                return {"data": {"users": [resolve_user(u, fields) for u in users]}}

            elif parsed["name"] == "user":
                user_id = parsed["args"].get("id")
                username = parsed["args"].get("username")
                if user_id:
                    user = User.query.get(user_id)
                elif username:
                    user = User.query.filter_by(username=username).first()
                else:
                    return {"errors": [{"message": "id or username required"}]}

                if not user:
                    return {"errors": [{"message": "User not found"}]}

                return {"data": {"user": resolve_user(user, fields)}}

            elif parsed["name"] == "posts":
                limit = parsed["args"].get("limit", 100)
                user_id = parsed["args"].get("user_id")
                query = Post.query
                if user_id:
                    query = query.filter_by(user_id=user_id)
                # VULNERABILITY: No privacy check - returns private posts
                posts = query.limit(limit).all()
                return {"data": {"posts": [resolve_post(p, fields) for p in posts]}}

            elif parsed["name"] == "post":
                post_id = parsed["args"].get("id")
                post = Post.query.get(post_id)
                if not post:
                    return {"errors": [{"message": "Post not found"}]}
                return {"data": {"post": resolve_post(post, fields)}}

            elif parsed["name"] == "messages":
                # VULNERABILITY: Can read any user's messages
                user_id = parsed["args"].get("user_id", current_user_id)
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
                return {"data": {"messages": result}}

            elif parsed["name"] == "search":
                q = parsed["args"].get("query", "")
                users = User.query.filter(User.username.like(f"%{q}%")).all()
                return {"data": {"search": [resolve_user(u, fields) for u in users]}}

            else:
                return {"errors": [{"message": f"Unknown query: {parsed['name']}"}]}

        # Handle mutations
        elif parsed["operation"] == "mutation":
            if parsed["name"] == "updateUserRole":
                # VULNERABILITY: No admin check - any user can change roles
                user_id = parsed["args"].get("user_id")
                new_role = parsed["args"].get("role")
                user = User.query.get(user_id)
                if not user:
                    return {"errors": [{"message": "User not found"}]}
                user.role = new_role
                db.session.commit()
                return {"data": {"updateUserRole": resolve_user(user, fields)}}

            elif parsed["name"] == "deleteUser":
                # VULNERABILITY: No admin check
                user_id = parsed["args"].get("user_id")
                user = User.query.get(user_id)
                if not user:
                    return {"errors": [{"message": "User not found"}]}
                username = user.username
                db.session.delete(user)
                db.session.commit()
                return {"data": {"deleteUser": f"User {username} deleted"}}

            elif parsed["name"] == "createPost":
                content = parsed["args"].get("content", "")
                is_public = parsed["args"].get("is_public", True)
                post = Post(user_id=current_user_id, content=content, is_public=is_public)
                db.session.add(post)
                db.session.commit()
                return {"data": {"createPost": resolve_post(post, fields)}}

            else:
                return {"errors": [{"message": f"Unknown mutation: {parsed['name']}"}]}

    except Exception as e:
        # VULNERABILITY: Verbose error messages
        return {
            "errors": [{"message": f"GraphQL execution error: {str(e)}"}],
            "query": query_str,
        }


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
    - Alias-based batching: many logical operations in one HTTP request (Stage 7.5)
    - Unbounded transport-level batch arrays (Stage 7.5)
    - Persisted-query allowlist bypass (Stage 7.5)
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
                "alias_attack": '{ u1: user(id: 1) { username role } u2: user(id: 2) { username role } u3: user(id: 3) { username role } }',
                "batch_array": '[{"query": "{ user(id: 1) { username } }"}, {"query": "{ user(id: 2) { username } }"}]  (send as top-level JSON array, not an object)',
                "persisted_query": '{"extensions": {"persistedQuery": {"sha256Hash": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"}}}',
            },
        }), 200

    raw = request.get_json()

    # VULNERABILITY (Batch Query DoS, Stage 7.5): transport-level batching -
    # if the POST body is a JSON array, each item is treated as its own
    # independent query document and processed in full, with NO limit on
    # how many items the array may contain. This is a real convention some
    # GraphQL clients/servers use (Apollo-style batching), and it means one
    # HTTP request can trigger an effectively unbounded number of database
    # operations, bypassing any control that only counts HTTP requests.
    if isinstance(raw, list):
        if len(raw) == 0:
            return jsonify({"errors": [{"message": "Empty batch"}]}), 400
        results = [_process_single_document(item, request.current_user_id) for item in raw]
        return jsonify(results), 200

    data = raw
    if not data or (not data.get("query") and not _extract_persisted_hash(data)):
        return jsonify({"errors": [{"message": "Query is required"}]}), 400

    response = _process_single_document(data, request.current_user_id)
    status = 200 if "errors" not in response or "data" in response else 400
    return jsonify(response), status

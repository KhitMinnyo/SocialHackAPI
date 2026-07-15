#!/usr/bin/env python3
"""
SocialHack API - Vulnerable Social Media API for Learning API Security
======================================================================

A deliberately vulnerable social media platform API designed for practicing
API hacking techniques. This application contains INTENTIONAL security
vulnerabilities for educational purposes.

⚠️  WARNING: This application is INTENTIONALLY VULNERABLE.
    DO NOT deploy this in production or on a public network.
    Use only in a controlled lab environment.

Usage:
    python run.py          # Start the API server
    python run.py --seed   # Seed database and start server
    python run.py --reset  # Reset database, seed, and start server

The API will be available at: http://localhost:5001
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.seed import seed_database

# Keep a reference to the started gRPC server so it is NOT garbage-collected
# (a grpc server with no live reference stops listening).
_GRPC_SERVER = None


def maybe_start_grpc_lab(reloader_active):
    """Auto-start the gRPC lab (grpc-lab/server.py) on :50051 in this process,
    so `python run.py` brings up BOTH the REST API (:5001) and gRPC (:50051).

    It stays optional and non-fatal:
      - if grpcio isn't installed -> print a hint and skip (REST app runs fine);
      - if the protobuf stubs are missing -> try to generate them, else skip;
      - opt out entirely with SOCIALHACK_GRPC=0.

    Under Flask's debug reloader the script runs twice (parent watcher + child
    worker); we only start gRPC in the worker to avoid a double bind on :50051.
    """
    if os.environ.get("SOCIALHACK_GRPC", "1") == "0":
        return
    # Only start in the worker process when the reloader is active.
    if reloader_active and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    grpc_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grpc-lab")
    if not os.path.isdir(grpc_dir):
        return

    try:
        import grpc  # noqa: F401
    except ImportError:
        print("  🔌 gRPC lab:        NOT started (grpcio not installed)")
        print("       enable with:   pip install -r grpc-lab/requirements.txt")
        return

    # Ensure the generated protobuf stubs exist; compile them if needed.
    pb2 = os.path.join(grpc_dir, "socialhack_pb2.py")
    pb2_grpc = os.path.join(grpc_dir, "socialhack_pb2_grpc.py")
    if not (os.path.exists(pb2) and os.path.exists(pb2_grpc)):
        try:
            import subprocess
            subprocess.run(
                [sys.executable, "-m", "grpc_tools.protoc", "-I.",
                 "--python_out=.", "--grpc_python_out=.", "socialhack.proto"],
                cwd=grpc_dir, check=True, capture_output=True,
            )
        except Exception as e:
            print(f"  🔌 gRPC lab:        NOT started (could not build stubs: {e})")
            print("       generate with: cd grpc-lab && python -m grpc_tools.protoc "
                  "-I. --python_out=. --grpc_python_out=. socialhack.proto")
            return

    if grpc_dir not in sys.path:
        sys.path.insert(0, grpc_dir)
    try:
        global _GRPC_SERVER
        import server as grpc_server  # grpc-lab/server.py
        _GRPC_SERVER = grpc_server.build_and_start(50051)  # keep ref alive!
        print("  🔌 gRPC lab:        localhost:50051 (UserService, reflection on, no auth)", flush=True)
    except Exception as e:
        print(f"  🔌 gRPC lab:        NOT started ({e})", flush=True)


def main():
    app = create_app()

    # Handle command line arguments
    should_seed = "--seed" in sys.argv or "--reset" in sys.argv
    should_reset = "--reset" in sys.argv

    with app.app_context():
        if should_reset:
            # Drop and recreate all tables
            print("[*] Resetting database...")
            db.drop_all()
            db.create_all()
            print("[+] Database reset complete.")

        if should_seed or should_reset:
            print("[*] Seeding database...")
            seed_database()
            print("[+] Database seeded.")
        elif not os.path.exists(os.path.join(os.path.dirname(__file__), "socialhack.db")):
            # Auto-seed if database doesn't exist
            print("[*] No database found. Creating and seeding...")
            db.create_all()
            seed_database()

    print()
    print("=" * 60)
    print("  🔓 SocialHack API - Vulnerable Social Media Platform")
    print("=" * 60)
    print()
    print("  ⚠️  WARNING: This API is INTENTIONALLY VULNERABLE!")
    print("  🌐 API running at: http://localhost:5001")
    print("  📖 API Info:       http://localhost:5001/")
    print("  🐛 Debug Info:     http://localhost:5001/api/v1/debug")
    print("  🖥️  Web UI:         http://localhost:5001/app")
    print("      (a real, click-through SocialHack frontend - browse it")
    print("       normally, or point Burp Suite at your browser and watch")
    print("       every click become a real /api/v1/* request - see")
    print("       Tutorial 2.5)")
    print()
    print("  Test Credentials:")
    print("  ─────────────────")
    print("  alice    / password123  (user)")
    print("  bob      / password123  (user)")
    print("  charlie  / password123  (user, private)")
    print("  admin    / admin123     (admin)")
    print("  diana    / diana2024!   (moderator)")
    print()
    print("=" * 60)
    print()

    # Auto-start the gRPC lab alongside the REST API (reloader is active
    # because debug=True below).
    maybe_start_grpc_lab(reloader_active=True)

    app.run(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    main()

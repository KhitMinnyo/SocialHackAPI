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

    app.run(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    main()

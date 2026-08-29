#!/usr/bin/env python3
"""
HTTP Method Analysis tool for the SocialHackAPI lab.

Logs in as a lab user, then probes a list of API endpoints with several
HTTP methods (GET/POST/PUT/PATCH/DELETE/OPTIONS) and reports every
(endpoint, method) combination the server accepts - i.e. anything other
than a plain 404/405. Handy for spotting an endpoint that quietly accepts
a method you didn't expect.

Two things are intentionally kept outside this file so the tool is easy
to keep up to date:
  - The endpoint list lives in endpoints.txt (same folder). Edit that
    file to add/remove endpoints without touching this script.
  - The target URL is a --url command-line flag instead of being
    hardcoded, so pointing this at a different lab instance (a new port,
    a different host, a remote box) is a one-flag change.

Usage:
    python3 endpoint_checker.py
    python3 endpoint_checker.py --url http://localhost:5001/api/v1
    python3 endpoint_checker.py --url http://192.168.1.50:5001/api/v1 --username bob --password password123
    python3 endpoint_checker.py --endpoints my-endpoints.txt
"""

import argparse
import os
import sys

import requests

DEFAULT_URL = "http://localhost:5001/api/v1"
DEFAULT_ENDPOINTS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "endpoints.txt"
)
HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Probe SocialHackAPI endpoints with multiple HTTP "
        "methods and report which combinations the server accepts."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Base API URL (default: {DEFAULT_URL}). Change this if the "
        "lab is running on a different host/port.",
    )
    parser.add_argument(
        "--endpoints",
        default=DEFAULT_ENDPOINTS_FILE,
        help="Path to the endpoint list, one path per line "
        f"(default: {DEFAULT_ENDPOINTS_FILE}).",
    )
    parser.add_argument(
        "--username", default="alice", help="Login username (default: alice)"
    )
    parser.add_argument(
        "--password",
        default="password123",
        help="Login password (default: password123)",
    )
    return parser.parse_args()


def load_endpoints(path):
    """Read the endpoint list from a text file, one path per line.

    Blank lines and lines starting with '#' are ignored, so the file can
    have its own header/comments.
    """
    with open(path, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def main():
    args = parse_args()
    base_url = args.url.rstrip("/")

    # First log in and get the token
    try:
        login_response = requests.post(
            f"{base_url}/auth/login",
            json={"username": args.username, "password": args.password},
            timeout=5,
        )
        login_response.raise_for_status()
        token = login_response.json()["token"]
    except Exception as exc:
        print(f"[!] Login to {base_url} failed: {exc}")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Endpoints to check - loaded from endpoints.txt
    try:
        endpoints = load_endpoints(args.endpoints)
    except OSError as exc:
        print(f"[!] Could not read endpoints file '{args.endpoints}': {exc}")
        sys.exit(1)

    print("=== HTTP Method Analysis ===")
    print(f"Target: {base_url}\n")

    for endpoint in endpoints:
        print(f"Endpoint: {endpoint}")
        for method in HTTP_METHODS:
            try:
                response = requests.request(
                    method,
                    f"{base_url}{endpoint}",
                    headers=headers,
                    json={"test": "data"},
                    timeout=5,
                )
                # 404 and 405 just mean that method doesn't work here, so
                # don't bother printing those
                if response.status_code not in (404, 405):
                    label = "OK" if response.status_code < 400 else "CHECK"
                    print(
                        f"  {label} {method}: "
                        f"{response.status_code} ({len(response.text)} bytes)"
                    )
            except Exception:
                # If this particular lab endpoint doesn't respond, keep
                # checking the rest
                pass
        print()


if __name__ == "__main__":
    main()

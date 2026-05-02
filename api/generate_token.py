#!/usr/bin/env python
"""Generate JWT tokens for api-news testing and deployment."""

import argparse
import os
import sys

from app.auth import generate_jwt_token


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate JWT tokens for api-news")
    parser.add_argument(
        "--secret",
        default=os.getenv("AUTH_JWT_SECRET"),
        help="JWT secret (default from AUTH_JWT_SECRET env var)",
    )
    parser.add_argument(
        "--expiry-hours",
        type=int,
        default=24,
        help="Token expiry in hours (default: 24)",
    )
    parser.add_argument(
        "--algorithm",
        default="HS256",
        help="JWT algorithm (default: HS256)",
    )

    args = parser.parse_args()

    if not args.secret or len(args.secret) < 32:
        print("Error: JWT secret must be at least 32 characters long.", file=sys.stderr)
        print("Set AUTH_JWT_SECRET or use --secret flag.", file=sys.stderr)
        sys.exit(1)

    token = generate_jwt_token(args.secret, args.algorithm, args.expiry_hours)
    print(f"✓ JWT Token (expires in {args.expiry_hours}h):")
    print(token)
    print("\nUsage:")
    print(f"  curl -H 'Authorization: Bearer {token}' https://api-news.../news?q=bitcoin")


if __name__ == "__main__":
    main()

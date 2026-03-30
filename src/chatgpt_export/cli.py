"""CLI entry point for chatgpt-export."""

from __future__ import annotations

import argparse
import sys

from chatgpt_export.auth import AuthError, build_headers, exchange_session_token
from chatgpt_export.client import APIClient, FatalAPIError
from chatgpt_export.exporter import ExportConfig, export_all


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="chatgpt-export",
        description="Export all ChatGPT conversations as markdown, organized by project folders.",
    )

    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument(
        "--token",
        help="ChatGPT access token (from browser network tab or DevTools)",
    )
    auth_group.add_argument(
        "--session-token",
        help="Session cookie value (__Secure-next-auth.session-token) to exchange for access token",
    )

    parser.add_argument(
        "--workspace-id",
        help="ChatGPT workspace/account ID (for team/enterprise)",
    )
    parser.add_argument(
        "--output-dir",
        default="./chatgpt-export-output",
        help="Output directory (default: ./chatgpt-export-output)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=3.0,
        help="Seconds between API requests (default: 3.0)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a previously interrupted export",
    )
    parser.add_argument(
        "--skip-projects",
        action="store_true",
        help="Only export root conversations (skip projects)",
    )
    parser.add_argument(
        "--skip-root",
        action="store_true",
        help="Only export project conversations (skip root)",
    )
    parser.add_argument(
        "--base-url",
        default="https://chatgpt.com",
        help="Base URL override (default: https://chatgpt.com)",
    )

    args = parser.parse_args(argv)

    # Resolve access token
    if args.token:
        access_token = args.token
    else:
        try:
            print("Exchanging session token for access token...")
            access_token = exchange_session_token(args.session_token, args.base_url)
            print("Token exchange successful.")
        except AuthError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    headers = build_headers(access_token, args.workspace_id)
    client = APIClient(
        headers=headers,
        base_url=args.base_url,
        rate_limit=args.rate_limit,
    )

    config = ExportConfig(
        output_dir=args.output_dir,
        skip_projects=args.skip_projects,
        skip_root=args.skip_root,
    )

    try:
        export_all(client, config)
    except FatalAPIError as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted. Progress has been saved. Use --resume to continue.")
        sys.exit(130)

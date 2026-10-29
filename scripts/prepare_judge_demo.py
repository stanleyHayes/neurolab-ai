"""Create isolated local judge settings without reading hosted credentials."""

import argparse
import os
import re
import secrets
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True, help="Dedicated local PostgreSQL database")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--output", type=Path, default=Path(".env.judge"))
    args = parser.parse_args()
    if not re.fullmatch(
        r"postgresql://(?:localhost(?::[0-9]+)?|127\.0\.0\.1(?::[0-9]+)?)?/[A-Za-z_][A-Za-z0-9_]*",
        args.database_url,
    ):
        parser.error("Use a dedicated local PostgreSQL database without embedded credentials")
    if not 1024 <= args.api_port <= 65535:
        parser.error("API port must be between 1024 and 65535")
    values = {
        "APP_ENV": "development",
        "DATABASE_URL": args.database_url,
        "RESEARCH_API_URL": f"http://127.0.0.1:{args.api_port}",
        "AUTH_INVITE_CODE": secrets.token_urlsafe(32),
        "MODEL_INFERENCE_ENABLED": "false",
        "RESEARCH_INLINE_WORKER": "false",
        "META_MODEL_API_KEY": "",
        "BASETEN_API_KEY": "",
        "MODEL_API_KEY": "",
        "API_BEARER_TOKEN": "",
    }
    # Exclusive creation preserves existing local configuration and private invites.
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")
    print(f"Created {args.output}; inference disabled, provider keys blank. No database created.")
    print("Use the private AUTH_INVITE_CODE in this file to register a local account.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import os
import sys
from urllib import request, error

API_KEY = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("JOB_DIGEST_FROM")
TO_EMAIL = os.environ.get("JOB_DIGEST_TO")


def main() -> int:
    if not API_KEY:
        print("Missing RESEND_API_KEY environment variable.")
        return 1
    if not FROM_EMAIL:
        print("Missing JOB_DIGEST_FROM environment variable.")
        return 1
    if not TO_EMAIL:
        print("Missing JOB_DIGEST_TO environment variable.")
        return 1

    payload = {
        "from": FROM_EMAIL,
        "to": [TO_EMAIL],
        "subject": "Resend API test",
        "html": "<p>This is a basic test email from the Resend API.</p>",
        "text": "This is a basic test email from the Resend API.",
    }

    req = request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            print(f"Status: {response.status}")
            print(body)
            return 0
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}")
        print(body)
        return exc.code
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

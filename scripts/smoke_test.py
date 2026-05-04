#!/usr/bin/env python3
"""
Smoke test for solvis-graphql-api.

Starts the Flask app directly (via `python -m solvis_graphql_api.solvis_graphql_api`)
and POSTs a GraphQL `about` query to http://localhost:5000/graphql.
No Docker, serverless CLI, DynamoDB, or S3 required — the 'about' resolver
reads only from the package version.

Usage:
    python scripts/smoke_test.py
    yarn smoke
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

# Add project root so we can import solvis_graphql_api
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
sys.path.insert(0, _project_root)


def log(msg: str) -> None:
    print(f"[smoke] {msg}", flush=True)


def wait_for_port(host: str, port: int, timeout: int = 30) -> bool:
    """Poll a TCP port until it accepts connections or timeout is reached."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://{host}:{port}/", timeout=2):
                return True
        except urllib.error.HTTPError:
            # Any HTTP response (404, 400, etc.) means the server is up
            return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(1)
    return False


def run() -> bool:
    log("Starting smoke test ...")

    os.chdir(_project_root)
    env = os.environ.copy()
    env.pop("LOGGING_CFG", None)

    proc = subprocess.Popen(
        [sys.executable, "-m", "solvis_graphql_api.solvis_graphql_api"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=_project_root,
    )

    try:
        if not wait_for_port("localhost", 5000):
            log("ERROR: Flask did not start in time.")
            return False

        payload = json.dumps({"query": "{ about }"}).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:5000/graphql",
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        log("Querying GraphQL 'about' ...")
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")

        log(f"HTTP {status} — {body}")

        if status != 200:
            log(f"FAIL: expected 200, got {status}")
            return False

        data = json.loads(body)
        about = data.get("data", {}).get("about", "")

        if "solvis_graphql_api" not in about:
            log(f"FAIL: 'about' missing 'solvis_graphql_api'. Got: {about!r}")
            return False

        if not re.search(r"\d+\.\d+", about):
            log(f"FAIL: 'about' missing version number. Got: {about!r}")
            return False

        log("PASS.")
        return True

    except Exception as exc:
        log(f"FAIL: {exc}")
        return False

    finally:
        proc.terminate()
        proc.wait(timeout=10)


if __name__ == "__main__":
    if not run():
        sys.exit(1)

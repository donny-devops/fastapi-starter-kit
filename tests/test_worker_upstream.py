"""Pin the Cloudflare Worker proxy to ORIGIN_URL's origin.

The Worker used `new URL(pathname, ORIGIN_URL)`. WHATWG URL treats a
protocol-relative path (`//evil.example/...`) as a different host, so a
request to `https://edge.example//evil.example/steal` would fetch the
attacker and forward the caller's Cookie header.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

WORKER = Path(__file__).resolve().parents[1] / "cloudflare" / "worker.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is required")

CASES = [
    (
        "https://edge.example/users/1",
        "https://api.example.com",
        "https://api.example.com/users/1",
    ),
    (
        "https://edge.example/auth/github/callback?code=abc",
        "https://api.example.com",
        "https://api.example.com/auth/github/callback?code=abc",
    ),
    (
        "https://edge.example//evil.example/steal",
        "https://api.example.com",
        None,
    ),
    (
        "https://edge.example/\\evil.example",
        "https://api.example.com",
        None,
    ),
    (
        "https://edge.example///evil.example",
        "http://localhost:8000",
        None,
    ),
]


def _resolve(request_url: str, origin_url: str) -> str | None:
    script = f"""
import {{ resolveUpstream }} from {WORKER.resolve().as_uri()!r};
const result = resolveUpstream({request_url!r}, {origin_url!r});
console.log(JSON.stringify(result ? result.href : null));
"""
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


@pytest.mark.parametrize("request_url,origin_url,expected", CASES)
def test_resolve_upstream_pins_origin(
    request_url: str, origin_url: str, expected: str | None
):
    assert _resolve(request_url, origin_url) == expected

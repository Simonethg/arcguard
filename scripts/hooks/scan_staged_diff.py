"""Block staged (or branch) content that looks like secrets or key material.

Patterns are concatenated at runtime so this file does not contain the
literals it rejects. Exits 1 when a path or an added diff line matches.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

MAX_BYTES = 50 * 1024 * 1024


def _p(*parts: str) -> str:
    return "".join(parts)


def _pattern(*parts: str) -> re.Pattern[str]:
    return re.compile(_p(*parts))


# Each tuple is (label, compiled pattern). Labels are safe to print.
CONTENT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("vendor-key", _pattern("sk", "-")),
    ("github-pat-classic", _pattern("ghp", "_")),
    ("github-pat-oauth", _pattern("gho", "_")),
    ("github-pat-fine", _pattern("github_pat", "_")),
    ("slack", _pattern("xox", "[abp]", "-")),
    ("aws-access-key", _pattern("AKI", "A")),
    ("google-api", _pattern("AIz", "a")),
    ("pem-header", _pattern("-----BEG", "IN")),
    ("jwt-prefix", _pattern("ey", "J")),
    ("password-assign", _pattern("password", "=")),
    ("secret-assign", _pattern("secret", "=")),
    ("token-assign", _pattern("token", "=")),
    ("seed-word", _pattern("mnemon", "ic")),
    ("hex-64", _pattern(r"[0-9a-fA-F]", "{64}")),
]

SENSITIVE_NAME = _pattern("mnemon", "ic")
SERVICE_ACCOUNT = re.compile(
    _p("service", "[-_]", "?", "account") + "|" + _p("serviceaccount"),
    re.IGNORECASE,
)


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _names(mode: str, base: str | None) -> list[str]:
    if mode == "cached":
        output = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    else:
        output = _git("diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD")
    return [line for line in output.splitlines() if line.strip()]


def _added_text(mode: str, base: str | None) -> str:
    if mode == "cached":
        output = _git("diff", "--cached", "--unified=0")
    else:
        output = _git("diff", "--unified=0", f"{base}...HEAD")
    added: list[str] = []
    for line in output.splitlines():
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith("+"):
            added.append(line[1:])
    return "\n".join(added)


def _blocked_name(path: str) -> str | None:
    name = path.rsplit("/", 1)[-1]
    lowered = name.lower()
    if lowered == ".env.example":
        return None
    if lowered == ".env" or lowered.startswith(".env."):
        return "env file"
    suffixes = (
        ".pem",
        ".p12",
        ".pfx",
        ".key",
        ".p8",
        ".jks",
        ".keystore",
        ".seed",
    )
    if lowered.endswith(suffixes) or "keystore" in lowered:
        return "key or keystore"
    if lowered in {"id_rsa", "id_ed25519", "id_ecdsa"} or lowered.startswith(
        ("id_rsa.", "id_ed25519.", "id_ecdsa.")
    ):
        return "private key"
    if lowered.endswith(".json") and (
        SERVICE_ACCOUNT.search(lowered)
        or lowered == "credentials.json"
        or lowered.endswith("-credentials.json")
        or lowered.startswith("client_secret")
        or lowered == "google-services.json"
    ):
        return "credential json"
    if SENSITIVE_NAME.search(lowered):
        return "seed phrase filename"
    return None


def _file_too_large(path: str, mode: str) -> bool:
    spec = f":{path}" if mode == "cached" else f"HEAD:{path}"
    completed = subprocess.run(
        ["git", "cat-file", "-s", spec],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return False
    try:
        size = int(completed.stdout.strip())
    except ValueError:
        return False
    return size > MAX_BYTES


def scan(mode: str, base: str | None) -> int:
    """Return 0 when the selected diff is clean."""

    failed = False
    for path in _names(mode, base):
        reason = _blocked_name(path)
        if reason is not None:
            print(f"blocked {reason}: {path}", file=sys.stderr)
            failed = True
        if _file_too_large(path, mode):
            print(f"blocked file over 50MB: {path}", file=sys.stderr)
            failed = True

    added = _added_text(mode, base)
    for label, pattern in CONTENT_PATTERNS:
        if pattern.search(added):
            print(f"blocked: diff matches secret pattern ({label})", file=sys.stderr)
            failed = True
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a git diff for secret material.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--cached",
        action="store_true",
        help="Scan the index (default).",
    )
    group.add_argument(
        "--range",
        metavar="BASE",
        help="Scan BASE...HEAD (commits on this branch).",
    )
    args = parser.parse_args(argv)
    if args.range:
        return scan("range", args.range)
    return scan("cached", None)


if __name__ == "__main__":
    raise SystemExit(main())

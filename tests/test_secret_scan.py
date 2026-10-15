"""Filename and diff-pattern checks used by the pre-commit hook."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "hooks" / "scan_staged_diff.py"
_SPEC = importlib.util.spec_from_file_location("scan_staged_diff", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_scan = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_scan)

CONTENT_PATTERNS = _scan.CONTENT_PATTERNS
_blocked_name = _scan._blocked_name


def test_env_example_is_the_only_env_file_allowed() -> None:
    assert _blocked_name(".env.example") is None
    assert _blocked_name("config/.env.example") is None
    assert _blocked_name(".env") == "env file"
    assert _blocked_name(".env.local") == "env file"


def test_key_material_filenames_are_blocked() -> None:
    assert _blocked_name("certs/server.pem") == "key or keystore"
    assert _blocked_name("app.p12") == "key or keystore"
    assert _blocked_name("release.keystore") == "key or keystore"
    assert _blocked_name("id_rsa") == "private key"
    assert _blocked_name("prod-service-account.json") == "credential json"
    assert _blocked_name("README.md") is None


def test_split_patterns_match_only_when_joined() -> None:
    patterns = dict(CONTENT_PATTERNS)
    assert patterns["vendor-key"].search("sk" + "-" + "example")
    assert patterns["password-assign"].search("password" + "=")
    assert patterns["seed-word"].search("mnemon" + "ic")
    assert patterns["hex-64"].search("ab" * 32)
    assert not patterns["hex-64"].search("ab" * 31)

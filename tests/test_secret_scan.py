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


HEX = "ab" * 32
URL = "https://explorer.testnet.arc.io/tx/0x" + HEX
EVIDENCE = "corpus/EVIDENCE.md"


def test_tx_url_allowed_only_in_evidence_file() -> None:
    assert _scan.scan_lines([(EVIDENCE, f"| ARC-005 | [tx]({URL}) |")]) == []


def test_bare_hex64_in_evidence_still_blocks() -> None:
    assert _scan.scan_lines([(EVIDENCE, f"| `0x{HEX}` |")]) == ["hex-64"]
    assert _scan.scan_lines([(EVIDENCE, f"[`0x{HEX}`]({URL})")]) == ["hex-64"]


def test_tx_url_in_other_file_still_blocks() -> None:
    assert _scan.scan_lines([("README.md", URL)]) == ["hex-64"]
    assert _scan.scan_lines([("corpus/other/EVIDENCE.md", URL)]) == ["hex-64"]


def test_other_hosts_or_longer_hex_not_allowed() -> None:
    assert _scan.scan_lines([(EVIDENCE, "https://evil.example/tx/0x" + HEX)]) == ["hex-64"]
    assert _scan.scan_lines([(EVIDENCE, URL + "ab")]) == ["hex-64"]


def test_key_value_blocks_even_when_allowlisted() -> None:
    key = "cd" * 32
    url = "https://explorer.testnet.arc.io/tx/0x" + key
    for k in (key, "0x" + key, "0x" + key.upper()):
        assert "ARC_TESTNET_PRIVATE_KEY value" in _scan.scan_lines([(EVIDENCE, url)], k)
        assert "ARC_TESTNET_PRIVATE_KEY value" in _scan.scan_lines([("a.txt", "x" + key)], k)
    assert _scan.scan_lines([(EVIDENCE, URL)], key) == []

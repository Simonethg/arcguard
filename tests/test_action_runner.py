"""Tests for the ArcGuard composite action runner and its text rules."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN_SCAN = ROOT / "action" / "run_scan.py"
REPORTS = ROOT / ".arcguard-test"


def _load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ENGINE = _load("arcguard_action_engine_test", "action/engine.py")
COMMENT = _load("arcguard_action_comment_test", "action/post_comment.py")


def _run(arguments: list[str], workspace: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GITHUB_WORKSPACE"] = str(workspace or ROOT)
    for key in (
        "GITHUB_OUTPUT",
        "ARCGUARD_REPORT_ONLY",
        "INPUT_PATH",
        "INPUT_FAIL_ON",
        "INPUT_SARIF_FILE",
        "INPUT_IGNORE",
    ):
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, str(RUN_SCAN), *arguments],
        cwd=str(workspace or ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _report_paths(name: str) -> tuple[Path, Path]:
    folder = REPORTS / name
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "out.sarif", folder / "out.md"


def test_vulnerable_fixture_fails_with_high_rules() -> None:
    sarif_path, markdown_path = _report_paths("vulnerable")
    completed = _run(
        [
            "--path",
            "action/fixtures/vulnerable",
            "--engine",
            "text",
            "--fail-on",
            "high",
            "--sarif",
            str(sarif_path.relative_to(ROOT)),
            "--markdown",
            str(markdown_path.relative_to(ROOT)),
        ]
    )
    assert completed.returncode == 1, completed.stderr
    payload = json.loads(sarif_path.read_text(encoding="utf-8"))
    assert payload["version"] == "2.1.0"
    rule_ids = {item["ruleId"] for item in payload["runs"][0]["results"]}
    assert {"ARC-001", "ARC-005", "ARC-007", "ARC-008", "ARC-OFF-1"} <= rule_ids
    assert "ARC-004" in rule_ids
    assert "ARC-006" in rule_ids
    for result in payload["runs"][0]["results"]:
        region = result["locations"][0]["physicalLocation"]["region"]
        assert region["startLine"] >= 1
        fingerprint = result["partialFingerprints"]["primaryLocationLineHash"]
        assert len(fingerprint) == 32
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "no certifica seguridad" in markdown
    assert "does not replace an audit" in markdown
    assert "https://docs.arc.io/arc/references/evm-differences" in markdown
    assert "docs/rules/ARC-005.md" in markdown
    assert "**Hallazgo:**" in markdown
    assert "**Finding:**" in markdown
    assert "**Arreglo:**" in markdown
    assert "**Fix:**" in markdown
    assert "address(0)" in markdown


def test_fixed_fixture_is_clean() -> None:
    sarif_path, markdown_path = _report_paths("fixed")
    completed = _run(
        [
            "--path",
            "action/fixtures/fixed",
            "--engine",
            "text",
            "--fail-on",
            "high",
            "--sarif",
            str(sarif_path.relative_to(ROOT)),
            "--markdown",
            str(markdown_path.relative_to(ROOT)),
        ]
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(sarif_path.read_text(encoding="utf-8"))
    assert payload["runs"][0]["results"] == []


def test_fail_on_none_exits_clean_when_findings_exist() -> None:
    sarif_path, markdown_path = _report_paths("fail-on-none")
    completed = _run(
        [
            "--path",
            "action/fixtures/vulnerable",
            "--engine",
            "text",
            "--fail-on",
            "none",
            "--sarif",
            str(sarif_path.relative_to(ROOT)),
            "--markdown",
            str(markdown_path.relative_to(ROOT)),
        ]
    )
    assert completed.returncode == 0, completed.stderr
    assert "should-fail=false" in completed.stdout


# Same list as .github/workflows/arcguard.yml. These trees are supposed to fail.
REPO_IGNORE = [
    "action/fixtures/vulnerable",
    "corpus/src/vulnerable",
    "corpus/test",
    "tests/fixtures/detectors",
    "corpus/*/*/vulnerable.*",
]


def _ignore_args() -> list[str]:
    arguments: list[str] = []
    for item in REPO_IGNORE:
        arguments.extend(["--ignore", item])
    return arguments


def test_repository_scan_ignores_the_vulnerable_fixture() -> None:
    sarif_path, markdown_path = _report_paths("repo")
    completed = _run(
        [
            "--path",
            ".",
            "--engine",
            "text",
            "--fail-on",
            "high",
            *_ignore_args(),
            "--sarif",
            str(sarif_path.relative_to(ROOT)),
            "--markdown",
            str(markdown_path.relative_to(ROOT)),
        ]
    )
    assert completed.returncode in {0, 1}, completed.stdout + completed.stderr
    payload = json.loads(sarif_path.read_text(encoding="utf-8"))
    uris = [
        item["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        for item in payload["runs"][0]["results"]
    ]
    assert all("action/fixtures/vulnerable" not in uri for uri in uris)
    assert all("corpus/src/vulnerable" not in uri for uri in uris)
    assert all(not uri.endswith("/vulnerable.sol") for uri in uris)
    assert all(not uri.endswith("/vulnerable.ts") for uri in uris)


def test_comments_do_not_count_as_code() -> None:
    workspace = REPORTS / "comments"
    workspace.mkdir(parents=True, exist_ok=True)
    source = workspace / "Noted.sol"
    source.write_text(
        "\n".join(
            [
                "// selfdestruct(payable(address(0)));",
                "/* block.prevrandao */",
                "contract Noted {",
                "    function ping() external pure returns (uint256) {",
                "        return 1;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    completed = _run(
        [
            "--path",
            "Noted.sol",
            "--engine",
            "text",
            "--fail-on",
            "high",
            "--sarif",
            "out.sarif",
            "--markdown",
            "out.md",
        ],
        workspace=workspace,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_fee_floor_boundary() -> None:
    below = ENGINE.scan_source("const maxFeePerGas = 19e9;\n", "script.js")
    floor = ENGINE.scan_source("const maxFeePerGas = 20e9;\n", "script.js")
    assert [item.rule.rule_id for item in below] == ["ARC-OFF-1"]
    assert floor == []


def test_scaled_mix_is_not_flagged() -> None:
    source = "\n".join(
        [
            "function mix(IERC20 usdc, uint256 price) external payable {",
            '    require(msg.value == price * 1e12, "scaled");',
            "    usdc.transfer(msg.sender, price);",
            "}",
        ]
    )
    assert ENGINE.scan_source(source, "Scaled.sol") == []


def test_scan_path_outside_the_workspace_is_rejected() -> None:
    sarif_path, markdown_path = _report_paths("escape")
    completed = _run(
        [
            "--path",
            "/etc",
            "--engine",
            "text",
            "--sarif",
            str(sarif_path.relative_to(ROOT)),
            "--markdown",
            str(markdown_path.relative_to(ROOT)),
        ]
    )
    assert completed.returncode == 2
    assert "workspace" in completed.stderr


def test_auto_engine_uses_cli_sarif_and_honors_ignore() -> None:
    if subprocess.run(["arcaudit", "--version"], capture_output=True, text=True).returncode != 0:
        pytest.skip("arcaudit is not installed")
    sarif_path, markdown_path = _report_paths("auto")
    vulnerable = _run(
        [
            "--path",
            "action/fixtures/vulnerable",
            "--engine",
            "auto",
            "--fail-on",
            "high",
            "--ignore",
            "action/fixtures/vulnerable",
            "--sarif",
            str(sarif_path.relative_to(ROOT)),
            "--markdown",
            str(markdown_path.relative_to(ROOT)),
        ]
    )
    assert vulnerable.returncode == 1, vulnerable.stdout + vulnerable.stderr
    assert "engine=arcaudit" in vulnerable.stdout
    assert "ARC-OFF-1" in vulnerable.stdout
    assert "should-fail=true" in vulnerable.stdout
    payload = json.loads(sarif_path.read_text(encoding="utf-8"))
    rule_ids = {item["ruleId"] for item in payload["runs"][0]["results"]}
    assert "ARC-OFF-1" in rule_ids
    summary = markdown_path.read_text(encoding="utf-8")
    assert "Hallazgo" in summary
    assert "docs/rules/ARC-OFF-1.md" in summary

    repo_sarif, repo_markdown = _report_paths("auto-repo")
    repo = _run(
        [
            "--path",
            ".",
            "--engine",
            "auto",
            "--fail-on",
            "high",
            *_ignore_args(),
            "--sarif",
            str(repo_sarif.relative_to(ROOT)),
            "--markdown",
            str(repo_markdown.relative_to(ROOT)),
        ]
    )
    assert repo.returncode == 0, repo.stdout + repo.stderr
    assert "engine=arcaudit" in repo.stdout
    assert "should-fail=false" in repo.stdout
    repo_payload = json.loads(repo_sarif.read_text(encoding="utf-8"))
    assert repo_payload["runs"][0]["results"] == []


def test_comment_updates_an_existing_marker() -> None:
    calls: list[tuple[str, str]] = []

    class _Response:
        def __init__(self, payload: object) -> None:
            self._payload = payload

        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        def read(self) -> bytes:
            return json.dumps(self._payload).encode("utf-8")

    def opener(request, timeout: int = 30):
        del timeout
        method = request.get_method()
        calls.append((method, request.full_url))
        if method == "GET":
            return _Response([{"id": 9, "body": '<!-- arcguard-summary path="." -->\nold'}])
        return _Response({"id": 9})

    result = COMMENT.upsert_comment(
        repository="Simonethg/arcguard",
        pr_number="7",
        markdown='<!-- arcguard-summary path="." -->\n\nhello\n',
        bearer="workflow",
        opener=opener,
    )
    assert result == "updated"
    assert calls[0][0] == "GET"
    assert calls[1][0] == "PATCH"
    assert calls[1][1].endswith("/issues/comments/9")


def test_action_manifests_are_composite() -> None:
    for relative in ("action.yml", "action/action.yml"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "using: composite" in text
        assert "run_scan.py" in text
        assert "upload-sarif" in text
        assert "continue-on-error: true" in text
        assert "post_comment.py" in text
        assert "always() && steps.scan.outputs.should-fail == 'true'" in text
        assert text.index("Upload SARIF") < text.index("Comment on the pull request")
        assert "security-severity" not in text
    root = (ROOT / "action.yml").read_text(encoding="utf-8")
    nested = (ROOT / "action" / "action.yml").read_text(encoding="utf-8")
    assert "ARCGUARD_HOME: ${{ github.action_path }}/action" in root
    assert "ARCGUARD_REPO: ${{ github.action_path }}/.." in nested


def test_readme_documents_the_action_in_spanish_and_english() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "uses: Simonethg/arcguard@v0" in readme
    assert "Code Scanning" in readme
    assert "pull-requests: write" in readme
    assert "security-events: write" in readme
    assert "no reemplaza una auditoría" in readme.lower() or "no certifica" in readme.lower()
    assert "does not replace an audit" in readme.lower()

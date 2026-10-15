"""Resolve a local path or a public GitHub URL to a directory or file."""

from __future__ import annotations

import re
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

_GITHUB_HTTPS = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/"
    r"(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?"
    r"(?:/(?P<kind>tree|blob)/(?P<ref>[^/]+)(?P<sub>/.*)?)?/?$",
    re.IGNORECASE,
)
_GITHUB_SSH = re.compile(
    r"^git@github\.com:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?$"
)


class TargetError(Exception):
    """The scan target is missing, unsupported, or could not be cloned."""


def parse_github(target: str) -> tuple[str, str | None, str | None] | None:
    """Return ``(clone_url, ref, subpath)`` or ``None`` when ``target`` is not GitHub.

    Credential URLs are rejected. Only ``github.com`` is accepted.
    """

    stripped = target.strip()
    if re.search(r"^[a-z]+://[^/]*@", stripped, re.IGNORECASE):
        raise TargetError("refusing a GitHub URL that embeds credentials")
    ssh = _GITHUB_SSH.fullmatch(stripped)
    if ssh:
        owner = ssh.group("owner")
        repo = ssh.group("repo")
        return f"git@github.com:{owner}/{repo}.git", None, None
    https = _GITHUB_HTTPS.fullmatch(stripped)
    if https is None:
        return None
    owner = https.group("owner")
    repo = https.group("repo")
    ref = https.group("ref")
    sub = https.group("sub")
    if ref and (ref.startswith("-") or ".." in ref.split("/")):
        raise TargetError("refusing a GitHub ref that looks like a flag or a parent path")
    subpath = None
    if sub:
        subpath = sub.lstrip("/")
        if not subpath:
            subpath = None
        elif ".." in Path(subpath).parts or subpath.startswith("-"):
            raise TargetError("refusing a GitHub path that escapes the repository")
    return f"https://github.com/{owner}/{repo}.git", ref, subpath


def _git_clone(clone_url: str, ref: str | None, dest: Path) -> None:
    command = [
        "git",
        "-c",
        "core.hooksPath=/dev/null",
        "clone",
        "--depth",
        "1",
    ]
    if ref:
        command.extend(["--branch", ref])
    command.extend([clone_url, str(dest)])
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise TargetError(f"could not clone {clone_url}") from exc


def resolve_target(
    target: str,
    *,
    cloner: Callable[[str, str | None, Path], None] = _git_clone,
) -> tuple[Path, Callable[[], None]]:
    """Return a filesystem path and a cleanup callback.

    An existing local path wins over a GitHub-shaped string. Public GitHub
    URLs are shallow-cloned with hooks disabled. The clone is deleted when
    the caller invokes the cleanup callback.
    """

    local = Path(target)
    if local.exists():
        return local, lambda: None
    parsed = parse_github(target)
    if parsed is None:
        raise TargetError(f"path does not exist: {target}")
    clone_url, ref, subpath = parsed
    temp = tempfile.TemporaryDirectory(prefix="arcaudit-")
    dest = Path(temp.name) / "repo"
    try:
        cloner(clone_url, ref, dest)
    except Exception:
        temp.cleanup()
        raise
    scan_root = dest if subpath is None else dest / subpath
    if not scan_root.exists():
        temp.cleanup()
        raise TargetError(f"cloned repository has no path {subpath}")
    return scan_root, temp.cleanup

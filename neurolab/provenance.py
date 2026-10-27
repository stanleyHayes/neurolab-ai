"""Loaded-source byte hashes and Git metadata, without executing commands."""

from __future__ import annotations

import hashlib
import os
import platform
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git_directory(root: Path) -> Path:
    path = root / ".git"
    if path.is_file():
        content = path.read_text(encoding="utf-8").strip()
        if not content.startswith("gitdir: "):
            raise ValueError("Unrecognized Git metadata")
        return (root / content[8:]).resolve()
    return path


def _resolve_revision(git: Path, head: str, depth=0):
    if depth > 8:
        return None
    if re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", head):
        return head
    if not head.startswith("ref: refs/"):
        return None
    reference = head[5:]
    common_file = git / "commondir"
    common = (git / common_file.read_text().strip()).resolve() if common_file.is_file() else git
    ref = (common / reference).resolve()
    if not ref.is_relative_to(common.resolve()):
        return None
    if ref.is_file():
        return _resolve_revision(git, ref.read_text().strip(), depth + 1)
    packed = common / "packed-refs"
    if packed.is_file():
        for line in packed.read_text().splitlines():
            fields = line.split()
            if len(fields) == 2 and fields[1] == reference:
                return _resolve_revision(git, fields[0], depth + 1)
    return None


def git_revision(root: Path):
    try:
        git = _git_directory(root)
        return _resolve_revision(git, (git / "HEAD").read_text().strip())
    except (OSError, ValueError):
        revision = os.getenv("VERCEL_GIT_COMMIT_SHA", "")
        return revision if re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", revision) else None


def capture_runtime_provenance():
    modules = [str(path.relative_to(ROOT)) for path in sorted((ROOT / "neurolab").glob("*.py"))] + [
        "schemas/agent_tool_call.schema.json"
    ]
    return {
        "snapshot": "API/module startup, not a claim about later filesystem edits",
        "code_commit": git_revision(ROOT),
        "worktree_dirty_at_startup": None,
        "dirty_status_note": "Not asserted by the application; exact relevant source-byte hashes are recorded.",
        "python_version": platform.python_version(),
        "module_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in modules
        },
    }


RUNTIME_PROVENANCE = capture_runtime_provenance()

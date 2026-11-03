"""Thin wrapper around the git command line."""

import subprocess


class GitError(Exception):
    """A git command failed, or the repository is not in a usable state."""


def run(args: list[str], cwd=None) -> str:
    """Run git with ``args`` and return stdout. Raise GitError on failure."""
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or f"git {' '.join(args)} failed"
        raise GitError(message)
    return proc.stdout


def succeeds(args: list[str], cwd=None) -> bool:
    """Run git with ``args`` and report whether it exited with status 0."""
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    return proc.returncode == 0

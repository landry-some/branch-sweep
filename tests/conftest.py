import os
import subprocess

import pytest


class Repo:
    """A throwaway git repository for tests."""

    def __init__(self, path):
        self.path = path
        self._counter = 0

    def git(self, *args) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.path, check=True,
            capture_output=True, text=True,
        ).stdout

    def commit(self, message="change") -> str:
        self._counter += 1
        (self.path / f"file{self._counter}.txt").write_text(message + "\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def branches(self) -> list[str]:
        out = self.git("for-each-ref", "--format=%(refname:short)", "refs/heads/")
        return sorted(out.split())


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch, tmp_path):
    # Keep the user's own git config (hooks, signing, default branch) out of tests.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Test Author")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "test@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Test Author")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "test@example.invalid")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repo on branch main with one commit; the test runs inside it."""
    path = tmp_path / "repo"
    path.mkdir()
    r = Repo(path)
    r.git("init", "-q", "-b", "main")
    r.commit("initial")
    monkeypatch.chdir(path)
    return r

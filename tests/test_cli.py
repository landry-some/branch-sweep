from branch_sweep.cli import main


def test_dry_run_lists_merged_branch(repo, capsys):
    repo.git("switch", "-q", "-c", "old")
    repo.commit("old work")
    repo.git("switch", "-q", "main")
    repo.git("merge", "-q", "--no-ff", "-m", "merge old", "old")

    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Base branch: main" in out
    assert "Would delete (1):\n  old\n" in out
    assert "old" in repo.branches()


def test_outside_repo_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    assert main([]) == 2
    assert "not inside a git repository" in capsys.readouterr().err


def test_protect_flag_is_repeatable(repo, capsys):
    for name in ("release/2", "keep", "gone"):
        repo.git("branch", name)
        repo.git("switch", "-q", name)
        repo.commit(name)
        repo.git("switch", "-q", "main")
        repo.git("merge", "-q", "--no-ff", "-m", f"merge {name}", name)

    assert main(["--protect", "release/*", "--protect", "keep"]) == 0
    out = capsys.readouterr().out
    assert "Would delete (1):\n  gone\n" in out
    assert "keep       protected" in out
    assert "release/2  protected" in out


def merged(repo, *names):
    for name in names:
        repo.git("switch", "-q", "-c", name)
        repo.commit(name)
        repo.git("switch", "-q", "main")
        repo.git("merge", "-q", "--no-ff", "-m", f"merge {name}", name)


def test_dry_run_changes_nothing(repo, capsys):
    merged(repo, "a", "b")
    assert main([]) == 0
    assert "Dry run, nothing deleted." in capsys.readouterr().out
    assert repo.branches() == ["a", "b", "main"]


def test_delete_with_yes(repo, capsys):
    merged(repo, "a", "b")
    repo.git("branch", "fresh")
    assert main(["--delete", "--yes"]) == 0
    out = capsys.readouterr().out
    assert "To delete (2):" in out
    assert "Deleted a\nDeleted b\n" in out
    assert repo.branches() == ["fresh", "main"]


def test_delete_asks_and_accepts_yes(repo, monkeypatch, capsys):
    merged(repo, "a")
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    assert main(["--delete"]) == 0
    assert repo.branches() == ["main"]


def test_delete_asks_and_defaults_to_no(repo, monkeypatch, capsys):
    merged(repo, "a")
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert main(["--delete"]) == 0
    assert "Cancelled, nothing deleted." in capsys.readouterr().out
    assert repo.branches() == ["a", "main"]


def test_delete_treats_closed_stdin_as_no(repo, monkeypatch):
    merged(repo, "a")

    def no_input(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", no_input)
    assert main(["--delete"]) == 0
    assert repo.branches() == ["a", "main"]


def test_nothing_to_delete_does_not_prompt(repo, monkeypatch, capsys):
    def fail(prompt):
        raise AssertionError("should not prompt")

    monkeypatch.setattr("builtins.input", fail)
    assert main(["--delete"]) == 0
    assert "Nothing to delete." in capsys.readouterr().out


def test_git_refusal_is_reported_and_exits_1(repo, capsys):
    # Merged into main, but HEAD is on another branch that lacks it,
    # so `git branch -d` refuses: the tool must report it, not force it.
    merged(repo, "a")
    repo.git("switch", "-q", "-c", "side", "HEAD~1")
    repo.commit("side work")
    assert main(["--delete", "--yes", "--base", "main"]) == 1
    captured = capsys.readouterr()
    assert "Failed  a:" in captured.err
    assert "a" in repo.branches()

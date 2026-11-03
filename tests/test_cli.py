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

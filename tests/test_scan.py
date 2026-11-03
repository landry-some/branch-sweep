import pytest

from branch_sweep.git import GitError
from branch_sweep.scan import build_plan, detect_base, merged_branches


def make_merged_branch(repo, name):
    repo.git("switch", "-q", "-c", name)
    repo.commit(f"work on {name}")
    repo.git("switch", "-q", "main")
    repo.git("merge", "-q", "--no-ff", "-m", f"merge {name}", name)


def test_detect_base_prefers_main(repo):
    repo.git("branch", "master")
    assert detect_base() == "main"


def test_detect_base_falls_back_to_master(repo):
    repo.git("branch", "-m", "main", "master")
    assert detect_base() == "master"


def test_detect_base_follows_origin_head(repo):
    repo.git("branch", "trunk")
    repo.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
    repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
    assert detect_base() == "trunk"


def test_detect_base_errors_without_candidates(repo):
    repo.git("branch", "-m", "main", "work")
    with pytest.raises(GitError, match="--base"):
        detect_base()


def test_merged_branches_excludes_unmerged(repo):
    make_merged_branch(repo, "feature/done")
    repo.git("switch", "-q", "-c", "feature/open")
    repo.commit("unfinished")
    repo.git("switch", "-q", "main")
    assert merged_branches("main") == ["feature/done", "main"]


def test_plan_keeps_base_and_lists_merged(repo):
    make_merged_branch(repo, "fix/a")
    make_merged_branch(repo, "fix/b")
    plan = build_plan("main")
    assert plan.delete == ["fix/a", "fix/b"]
    assert plan.kept == [("main", "base branch")]


def test_plan_rejects_missing_base(repo):
    with pytest.raises(GitError, match="does not exist"):
        build_plan("nope")

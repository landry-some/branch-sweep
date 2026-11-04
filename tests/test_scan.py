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
    assert [b.name for b in merged_branches("main")] == ["feature/done", "main"]


def test_plan_keeps_base_and_lists_merged(repo):
    make_merged_branch(repo, "fix/a")
    make_merged_branch(repo, "fix/b")
    plan = build_plan("main")
    assert plan.delete == ["fix/a", "fix/b"]
    assert plan.kept == [("main", "base branch")]


def test_plan_rejects_missing_base(repo):
    with pytest.raises(GitError, match="does not exist"):
        build_plan("nope")


def test_well_known_names_are_protected(repo):
    for name in ("master", "develop", "trunk"):
        repo.git("branch", name)
    make_merged_branch(repo, "topic")
    plan = build_plan("main")
    assert plan.delete == ["topic"]
    assert ("develop", "protected") in plan.kept
    assert ("master", "protected") in plan.kept
    assert ("trunk", "protected") in plan.kept


def test_protect_patterns_from_argument(repo):
    make_merged_branch(repo, "release/1.0")
    make_merged_branch(repo, "topic")
    plan = build_plan("main", protect=["release/*"])
    assert plan.delete == ["topic"]
    assert ("release/1.0", "protected") in plan.kept


def test_protect_patterns_from_git_config(repo):
    make_merged_branch(repo, "keep-me")
    make_merged_branch(repo, "hotfix/x")
    make_merged_branch(repo, "topic")
    repo.git("config", "--add", "branch-sweep.protect", "keep-*")
    repo.git("config", "--add", "branch-sweep.protect", "hotfix/*")
    plan = build_plan("main")
    assert plan.delete == ["topic"]
    assert {name for name, _ in plan.kept} == {"main", "keep-me", "hotfix/x"}


def test_protected_base_is_reported_as_base(repo):
    assert build_plan("main").kept == [("main", "base branch")]


def test_current_branch_is_kept(repo):
    make_merged_branch(repo, "topic")
    repo.git("switch", "-q", "topic")
    plan = build_plan("main")
    assert plan.delete == []
    assert ("topic", "current branch") in plan.kept


def test_branch_in_other_worktree_is_kept(repo, tmp_path):
    make_merged_branch(repo, "topic")
    make_merged_branch(repo, "other")
    repo.git("worktree", "add", "-q", str(tmp_path / "wt"), "topic")
    plan = build_plan("main")
    assert plan.delete == ["other"]
    assert ("topic", "checked out in a worktree") in plan.kept


def test_branch_at_base_commit_is_kept(repo):
    repo.git("branch", "fresh")
    make_merged_branch(repo, "done")
    repo.git("branch", "fresh-too")
    plan = build_plan("main")
    # "fresh" is behind main now, so it is an old merged pointer: delete it.
    assert plan.delete == ["done", "fresh"]
    assert ("fresh-too", "same commit as main (probably just created)") in plan.kept


def test_detached_head_does_not_crash(repo):
    make_merged_branch(repo, "topic")
    repo.git("switch", "-q", "--detach", "HEAD~1")
    assert build_plan("main").delete == ["topic"]


def test_merged_branches_reads_tips(repo):
    make_merged_branch(repo, "topic")
    tips = {b.name: b.tip for b in merged_branches("main")}
    assert tips["topic"] == repo.git("rev-parse", "topic").strip()
    assert tips["main"] == repo.git("rev-parse", "main").strip()


def test_min_age_keeps_recent_branches(repo, monkeypatch):
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-01-01T12:00:00Z")
    make_merged_branch(repo, "old")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-01-25T12:00:00Z")
    make_merged_branch(repo, "recent")
    now = repo_time(repo, "recent") + 5 * 86400
    plan = build_plan("main", min_age=10, now=now)
    assert plan.delete == ["old"]
    assert ("recent", "last commit 5 days ago (--min-age 10)") in plan.kept


def test_min_age_zero_keeps_nothing_extra(repo):
    make_merged_branch(repo, "topic")
    assert build_plan("main", min_age=0).delete == ["topic"]


def repo_time(repo, ref):
    return int(repo.git("log", "-1", "--format=%ct", ref).strip())

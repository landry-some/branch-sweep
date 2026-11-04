"""Work out which local branches can be deleted, and why the others are kept."""

from dataclasses import dataclass, field
from fnmatch import fnmatchcase

from .git import GitError, run, succeeds

HEADS = "refs/heads/"
ALWAYS_PROTECTED = ("main", "master", "develop", "trunk")


@dataclass(frozen=True)
class Branch:
    name: str
    tip: str


@dataclass
class Plan:
    base: str
    delete: list[str] = field(default_factory=list)
    kept: list[tuple[str, str]] = field(default_factory=list)


def ensure_repo(cwd=None) -> None:
    if not succeeds(["rev-parse", "--git-dir"], cwd):
        raise GitError("not inside a git repository")


def branch_exists(name: str, cwd=None) -> bool:
    return succeeds(["show-ref", "--verify", "--quiet", HEADS + name], cwd)


def detect_base(cwd=None) -> str:
    """Pick the base branch: origin/HEAD's target, else main, else master."""
    if succeeds(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd):
        target = run(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd).strip()
        name = target.removeprefix("refs/remotes/origin/")
        if branch_exists(name, cwd):
            return name
    for name in ("main", "master"):
        if branch_exists(name, cwd):
            return name
    raise GitError("could not find a base branch, pass one with --base")


def merged_branches(base: str, cwd=None) -> list[Branch]:
    """Local branches whose tip is reachable from ``base``, sorted by name.

    Everything is read in a single ``git for-each-ref`` call.
    """
    out = run(
        [
            "for-each-ref", f"--merged={HEADS}{base}",
            "--format=%(objectname) %(refname)", HEADS,
        ],
        cwd,
    )
    branches = []
    for line in out.splitlines():
        if line:
            sha, ref = line.split(" ", 1)
            branches.append(Branch(ref.removeprefix(HEADS), sha))
    return sorted(branches, key=lambda b: b.name)


def configured_patterns(cwd=None) -> list[str]:
    """Patterns from the multi-valued ``branch-sweep.protect`` git config."""
    if not succeeds(["config", "--get-all", "branch-sweep.protect"], cwd):
        return []
    out = run(["config", "--get-all", "branch-sweep.protect"], cwd)
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_protected(name: str, patterns) -> bool:
    if name in ALWAYS_PROTECTED:
        return True
    return any(fnmatchcase(name, pattern) for pattern in patterns)


def current_branch(cwd=None) -> str | None:
    """Name of the checked-out branch, or None on a detached HEAD."""
    if not succeeds(["symbolic-ref", "--quiet", "HEAD"], cwd):
        return None
    return run(["symbolic-ref", "HEAD"], cwd).strip().removeprefix(HEADS)


def worktree_branches(cwd=None) -> set[str]:
    """Branches checked out in any worktree of this repository."""
    out = run(["worktree", "list", "--porcelain"], cwd)
    return {
        line.removeprefix("branch ").removeprefix(HEADS)
        for line in out.splitlines()
        if line.startswith("branch ")
    }


def tip(name: str, cwd=None) -> str:
    return run(["rev-parse", HEADS + name], cwd).strip()


def build_plan(base: str, protect=(), cwd=None) -> Plan:
    if not branch_exists(base, cwd):
        raise GitError(f"base branch '{base}' does not exist")
    patterns = [*protect, *configured_patterns(cwd)]
    current = current_branch(cwd)
    in_worktrees = worktree_branches(cwd)
    base_tip = tip(base, cwd)
    plan = Plan(base=base)
    for branch in merged_branches(base, cwd):
        name = branch.name
        reason = None
        if name == base:
            reason = "base branch"
        elif is_protected(name, patterns):
            reason = "protected"
        elif name == current:
            reason = "current branch"
        elif name in in_worktrees:
            reason = "checked out in a worktree"
        elif branch.tip == base_tip:
            reason = f"same commit as {base} (probably just created)"
        if reason:
            plan.kept.append((name, reason))
        else:
            plan.delete.append(name)
    return plan


def delete_branch(name: str, cwd=None) -> None:
    """Delete with ``git branch -d`` so git refuses anything not fully merged."""
    run(["branch", "-d", name], cwd)

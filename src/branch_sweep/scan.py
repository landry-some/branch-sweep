"""Work out which local branches can be deleted, and why the others are kept."""

from dataclasses import dataclass, field

from .git import GitError, run, succeeds

HEADS = "refs/heads/"


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


def merged_branches(base: str, cwd=None) -> list[str]:
    """Local branches whose tip is reachable from ``base``, sorted by name."""
    out = run(
        ["for-each-ref", f"--merged={HEADS}{base}", "--format=%(refname)", HEADS],
        cwd,
    )
    return sorted(line.removeprefix(HEADS) for line in out.splitlines() if line)


def build_plan(base: str, cwd=None) -> Plan:
    if not branch_exists(base, cwd):
        raise GitError(f"base branch '{base}' does not exist")
    plan = Plan(base=base)
    for name in merged_branches(base, cwd):
        if name == base:
            plan.kept.append((name, "base branch"))
        else:
            plan.delete.append(name)
    return plan

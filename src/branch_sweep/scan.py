"""Work out which local branches can be deleted, and why the others are kept."""

from dataclasses import dataclass, field
from fnmatch import fnmatchcase

from .git import GitError, run, succeeds

HEADS = "refs/heads/"
ALWAYS_PROTECTED = ("main", "master", "develop", "trunk")


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


def build_plan(base: str, protect=(), cwd=None) -> Plan:
    if not branch_exists(base, cwd):
        raise GitError(f"base branch '{base}' does not exist")
    patterns = [*protect, *configured_patterns(cwd)]
    plan = Plan(base=base)
    for name in merged_branches(base, cwd):
        if name == base:
            plan.kept.append((name, "base branch"))
        elif is_protected(name, patterns):
            plan.kept.append((name, "protected"))
        else:
            plan.delete.append(name)
    return plan

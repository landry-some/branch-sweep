"""Command-line entry point."""

import argparse
import sys

from . import __version__
from .git import GitError
from .scan import Plan, build_plan, delete_branch, detect_base, ensure_repo


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="branch-sweep",
        description="Show (and optionally delete) local branches already "
        "merged into the base branch.",
    )
    parser.add_argument(
        "--base", metavar="BRANCH",
        help="branch to compare against (default: origin/HEAD, main or master)",
    )
    parser.add_argument(
        "--protect", metavar="PATTERN", action="append", default=[],
        help="never delete branches matching this glob (repeatable)",
    )
    parser.add_argument(
        "--delete", action="store_true",
        help="delete the listed branches (asks first unless --yes)",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="with --delete, do not ask for confirmation",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser.parse_args(argv)


def print_plan(plan: Plan, deleting: bool) -> None:
    print(f"Base branch: {plan.base}")
    print()
    if plan.delete:
        heading = "To delete" if deleting else "Would delete"
        print(f"{heading} ({len(plan.delete)}):")
        for name in plan.delete:
            print(f"  {name}")
    else:
        print("Nothing to delete.")
    if plan.kept:
        width = max(len(name) for name, _ in plan.kept)
        print()
        print(f"Kept ({len(plan.kept)}):")
        for name, reason in plan.kept:
            print(f"  {name:<{width}}  {reason}")


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        ensure_repo()
        base = args.base or detect_base()
        plan = build_plan(base, protect=args.protect)
    except GitError as err:
        print(f"branch-sweep: {err}", file=sys.stderr)
        return 2
    print_plan(plan, deleting=args.delete)

    if not plan.delete:
        return 0
    if not args.delete:
        print()
        print("Dry run, nothing deleted. Run with --delete to remove them.")
        return 0
    if not args.yes and not confirm(len(plan.delete)):
        print("Cancelled, nothing deleted.")
        return 0

    print()
    failed = 0
    for name in plan.delete:
        try:
            delete_branch(name)
        except GitError as err:
            failed += 1
            print(f"Failed  {name}: {err}", file=sys.stderr)
        else:
            print(f"Deleted {name}")
    return 1 if failed else 0


def confirm(count: int) -> bool:
    print()
    try:
        answer = input(f"Delete {count} branch{'es' if count != 1 else ''}? [y/N] ")
    except EOFError:
        print()
        return False
    return answer.strip().lower() in ("y", "yes")


if __name__ == "__main__":
    sys.exit(main())

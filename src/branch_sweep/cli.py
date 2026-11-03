"""Command-line entry point."""

import argparse
import sys

from . import __version__
from .git import GitError
from .scan import Plan, build_plan, detect_base, ensure_repo


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
    parser.add_argument("--version", action="version", version=__version__)
    return parser.parse_args(argv)


def print_plan(plan: Plan) -> None:
    print(f"Base branch: {plan.base}")
    print()
    if plan.delete:
        print(f"Would delete ({len(plan.delete)}):")
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
    print_plan(plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# branch-sweep

A small command-line tool that finds local git branches already merged into your
main branch and deletes them, but only after showing you the list and the reason
each other branch was left alone.

`git branch --merged` gets you most of the way, but its output also includes the
branch you are on, `main` itself, branches checked out in another worktree, and
branches you created a minute ago that have no commits yet. `branch-sweep` filters
those out and tells you why.

## Who it's for

Developers who keep many short-lived local branches and want a quick, safe cleanup
without writing a shell one-liner each time.

## Built with

Python 3.11+ and the standard library only. It runs the `git` command-line tool for
every check and uses `git branch -d` for deletion, so git's own "not fully merged"
guard still applies. Tests use pytest and build real throwaway repositories.

## Install

Needs Python 3.11 or newer and git.

```bash
git clone https://github.com/landry-some/branch-sweep.git
cd branch-sweep
python3 -m venv .venv
.venv/bin/pip install -e .
```

This puts the `branch-sweep` command in `.venv/bin/`. Activate the venv
(`source .venv/bin/activate`) or call `.venv/bin/branch-sweep` directly.

## Usage

Run it inside any git repository:

```bash
branch-sweep                 # dry run: show what would be deleted and what is kept
branch-sweep --delete        # same list, then ask y/N and delete
branch-sweep --delete --yes  # delete without asking
```

Example output:

```
Base branch: main

Would delete (2):
  feature/login-form
  fix/typo-in-footer

Kept (3):
  main              base branch
  spike/new-parser  same commit as main (probably just created)
  wip/search        checked out in a worktree

Dry run, nothing deleted. Run with --delete to remove them.
```

### Options

| Option | What it does |
|---|---|
| `--base BRANCH` | Branch to compare against. Default: the branch `origin/HEAD` points to, else `main`, else `master`. |
| `--protect PATTERN` | Never delete branches matching this glob (e.g. `release/*`). Can be repeated. |
| `--delete` | Actually delete the candidates (asks first). Without it, nothing is changed. |
| `--yes`, `-y` | With `--delete`, skip the confirmation prompt. |

### What is never deleted

- The base branch, and `main`, `master`, `develop` and `trunk`.
- Branches matching a `--protect` pattern or the `branch-sweep.protect` git config
  (multi-valued, so you can add several):

  ```bash
  git config --add branch-sweep.protect 'release/*'
  git config --add branch-sweep.protect 'keep-*'
  ```

- The current branch and any branch checked out in a linked worktree.
- Branches still pointing at the same commit as the base, since they are most
  likely new branches with no work yet.

Exit codes: `0` on success, `1` if a deletion failed, `2` for usage errors or when
not inside a git repository.

## Tests

```bash
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

## Plans

See [ROADMAP.md](ROADMAP.md).

## License

MIT, see [LICENSE](LICENSE).

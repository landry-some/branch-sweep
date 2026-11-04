# Roadmap

Work planned after v0.1. Estimates are rough, in hours. Total: **30.5 h**.

## Features (17 h)

- [ ] Detect squash- and rebase-merged branches (compare patch IDs with `git cherry`) — 4 h
- [ ] `--remote <name>`: also delete merged branches on a remote (`git push --delete`), with the same dry run — 3 h
- [ ] Restore log: write each deleted branch's tip to a log file, plus a `branch-sweep restore <name>` command — 3 h
- [ ] Interactive mode: pick which candidates to delete from a checklist — 2.5 h
- [ ] List branches whose upstream is gone (`[gone]`) as a separate group — 2 h
- [x] `--min-age DAYS`: only sweep branches whose last commit is older than N days — 1.5 h
- [ ] `--json` output for scripting — 1 h

## Bugs and edge cases (4 h)

- [ ] Clear messages for detached HEAD, a repo with no commits, and no base branch found — 1.5 h
- [ ] Branch names with slashes, dots and non-ASCII characters in all output paths — 1 h
- [ ] Bare repositories and linked worktrees run from inside the worktree — 1.5 h

## Refactors (3 h)

- [x] Read all branch data in one `git for-each-ref` call instead of one call per branch — 2 h
- [ ] Split the plan (what to delete and why) from terminal output, so JSON and text share it — 1 h

## Tests (4 h)

- [ ] GitHub Actions CI on Linux, macOS and Windows with Python 3.11–3.13 — 2 h
- [ ] Test fixtures for squash, rebase and fast-forward merges — 2 h

## Docs (2.5 h)

- [ ] README recipes (git alias, weekly cleanup, protecting release branches) — 1.5 h
- [ ] CHANGELOG.md, starting at 0.1.0 — 1 h

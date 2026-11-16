# tcps migration plan v26.11.16

Standing: UNVERIFIED

## Identity
- path: /Users/sac/tcps
- remote: https://github.com/seanchatmangpt/tcps (fork of github/spec-kit)
- branch@sha: main@852735d, last commit 2026-09-18, 1806 commits, 44 MB
- languages/build: Python (pyproject.toml, uv.lock), templates/, extensions/
- nested repos: none

## Observed state
- dirty=0; untracked=11: docs/jira/ (v26.9.19 catalogue)
- ahead 11 / behind 74 origin/main. The 11 ahead are merges of upstream community PRs
  (extension catalog entries, star-history) plus "exp: extension script parity invariant".
- unpushed branch: exp/extension-script-parity @2301831 (its commit is already merged into
  main)
- stash 0; build dirs: none (.venv absent)
- submodules: none

## What it is
Fork of GitHub Spec Kit (spec-driven development toolkit for AI coding agents), renamed tcps,
with a local experiment adding a structural parity invariant for bundled extension scripts.

## Classification
ACTIVE per census; evidence says WARM (no commits since 2026-09-18, mostly upstream merges).

## Migration risk
LOW-MEDIUM. 11 local commits not on origin; otherwise clean.

## Recommended action
COMMIT-PUSH
1. `git add docs/jira && git commit -m "docs: v26.11.16 catalogue"`
2. `git push origin main` (and `git push -u origin exp/extension-script-parity`, optional).
3. Re-clone on the new machine.

## First commands on the new machine
`uv sync && uv run pytest`

## See Also
- ../v26.9.19/
- /Users/sac/docs/jira/v26.11.16/README.md

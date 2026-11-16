# tcps: land or delete remote branch `benbtg/add-star-history`

- Standing: OPEN
- Created: 2026-09-19 (v26.9.19 gh survey wave)
- Source: remote branch `benbtg/add-star-history` — not merged into `main`, no open PR
- Evidence: `git branch -r --no-merged origin/main` lists it; absent from `gh pr list` heads

## Work to complete
- Decide: open a PR (`gh pr create -R seanchatmangpt/tcps --head benbtg/add-star-history`) or delete (`git push origin --delete benbtg/add-star-history`).
- If superseded, delete; otherwise land through review.

## Acceptance
- After `git fetch --prune`, `git branch -r --no-merged origin/main` no longer lists `benbtg/add-star-history`.

## History
- 2026-09-19 | OPEN | survey found PR-less unmerged branch | benbtg/add-star-history | decision pending

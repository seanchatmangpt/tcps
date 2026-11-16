# tcps: land or delete remote branch `copilot/fix-review-comments-again`

- Standing: OPEN
- Created: 2026-09-19 (v26.9.19 gh survey wave)
- Source: remote branch `copilot/fix-review-comments-again` — not merged into `main`, no open PR
- Evidence: `git branch -r --no-merged origin/main` lists it; absent from `gh pr list` heads

## Work to complete
- Decide: open a PR (`gh pr create -R seanchatmangpt/tcps --head copilot/fix-review-comments-again`) or delete (`git push origin --delete copilot/fix-review-comments-again`).
- If superseded, delete; otherwise land through review.

## Acceptance
- After `git fetch --prune`, `git branch -r --no-merged origin/main` no longer lists `copilot/fix-review-comments-again`.

## History
- 2026-09-19 | OPEN | survey found PR-less unmerged branch | copilot/fix-review-comments-again | decision pending

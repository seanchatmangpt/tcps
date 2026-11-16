# tcps: land or delete remote branch `add-axi-extension-5424edb2e2fda191`

- Standing: OPEN
- Created: 2026-09-19 (v26.9.19 gh survey wave)
- Source: remote branch `add-axi-extension-5424edb2e2fda191` — not merged into `main`, no open PR
- Evidence: `git branch -r --no-merged origin/main` lists it; absent from `gh pr list` heads

## Work to complete
- Decide: open a PR (`gh pr create -R seanchatmangpt/tcps --head add-axi-extension-5424edb2e2fda191`) or delete (`git push origin --delete add-axi-extension-5424edb2e2fda191`).
- If superseded, delete; otherwise land through review.

## Acceptance
- After `git fetch --prune`, `git branch -r --no-merged origin/main` no longer lists `add-axi-extension-5424edb2e2fda191`.

## History
- 2026-09-19 | OPEN | survey found PR-less unmerged branch | add-axi-extension-5424edb2e2fda191 | decision pending

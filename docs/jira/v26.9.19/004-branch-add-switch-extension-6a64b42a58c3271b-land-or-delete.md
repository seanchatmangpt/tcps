# tcps: land or delete remote branch `add-switch-extension-6a64b42a58c3271b`

- Standing: OPEN
- Created: 2026-09-19 (v26.9.19 gh survey wave)
- Source: remote branch `add-switch-extension-6a64b42a58c3271b` — not merged into `main`, no open PR
- Evidence: `git branch -r --no-merged origin/main` lists it; absent from `gh pr list` heads

## Work to complete
- Decide: open a PR (`gh pr create -R seanchatmangpt/tcps --head add-switch-extension-6a64b42a58c3271b`) or delete (`git push origin --delete add-switch-extension-6a64b42a58c3271b`).
- If superseded, delete; otherwise land through review.

## Acceptance
- After `git fetch --prune`, `git branch -r --no-merged origin/main` no longer lists `add-switch-extension-6a64b42a58c3271b`.

## History
- 2026-09-19 | OPEN | survey found PR-less unmerged branch | add-switch-extension-6a64b42a58c3271b | decision pending

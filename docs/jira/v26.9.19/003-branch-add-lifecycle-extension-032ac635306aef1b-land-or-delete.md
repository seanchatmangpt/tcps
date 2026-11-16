# tcps: land or delete remote branch `add-lifecycle-extension-032ac635306aef1b`

- Standing: OPEN
- Created: 2026-09-19 (v26.9.19 gh survey wave)
- Source: remote branch `add-lifecycle-extension-032ac635306aef1b` — not merged into `main`, no open PR
- Evidence: `git branch -r --no-merged origin/main` lists it; absent from `gh pr list` heads

## Work to complete
- Decide: open a PR (`gh pr create -R seanchatmangpt/tcps --head add-lifecycle-extension-032ac635306aef1b`) or delete (`git push origin --delete add-lifecycle-extension-032ac635306aef1b`).
- If superseded, delete; otherwise land through review.

## Acceptance
- After `git fetch --prune`, `git branch -r --no-merged origin/main` no longer lists `add-lifecycle-extension-032ac635306aef1b`.

## History
- 2026-09-19 | OPEN | survey found PR-less unmerged branch | add-lifecycle-extension-032ac635306aef1b | decision pending

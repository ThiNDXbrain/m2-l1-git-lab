# Git workflow

Notes for the M2-L1 Git lab.

## Branch naming

`l1/<learner-id>/<lab>` — for example `l1/LRN-66519dd7/m2-l1`.

## Steps

1. Create a branch from `main`: `git switch -c l1/LRN-66519dd7/m2-l1`
2. Commit the change with a message that says what changed and why.
3. Push the branch: `git push -u origin l1/LRN-66519dd7/m2-l1`
4. Open a pull request into `main` and ask for a review.
5. Do not self-merge. A reviewer verifies and merges.

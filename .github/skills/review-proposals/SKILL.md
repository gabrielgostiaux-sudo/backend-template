---
name: review-proposals
description: project-master only. Reviews open scope-proposal issues from every agent (its own included) - approves, amends, rejects or asks - and, once the user explicitly approves, applies profile, repository-profile, corpus and other .github changes, logs each in .changes/github/ or .changes/context/, and opens one PR. Use whenever such issues are open.
---

# /review-proposals

**`project-master` runs this.** Any other agent: stop and say so.

## 1. Collect

`gh issue list --label scope-proposal --state open --json number,title,body,author,createdAt,comments`, oldest first.

## 2. Recommend a decision for each proposal

Check it against:
- **The corpus**, which wins over preferences. A correction of fact belongs in the corpus, followed by a
  `cloud-init refresh`, not in a profile edit that the next refresh would overwrite.
- **The other agents.** No two agents own the same thing, and the interfaces and handoffs match on both sides.
- **Form.** Template structure, size limits, specific content (paths, commands, IDs), tags kept.
- **Design content** (architecture, data, delivery, security): ask the matching cloud agent first, with a handoff note.

Recommend one of:

| Decision | Meaning |
|---|---|
| approve | Apply as proposed. |
| amend | Apply a corrected version (say what you changed). |
| reject | Don't apply; give the reason and the alternative. |
| needs-info | Ask the proposer one precise question; leave the issue open. |

## 3. Ask the user

Present every proposal with your recommendation and the exact change. The user decides. Apply nothing under `.github/`
or `.corpus/` without the user's explicit yes for that proposal. Unattended, stop here and leave the summary as a
comment on each issue.

## 4. Apply the approved ones (one branch per review session)

1. `git switch -c dev-<first-proposal>-scope-review` from up-to-date `dev`.
2. Apply:
   - profiles and the repository profile: write the body to a temp file outside the repo, then
     `python3 .github/scripts/profiles.py set <key> <file>`. Keep `OWNER NOTES` verbatim unless the proposal
     targets them;
   - corpus: edit the file and keep its front matter, IDs and tags;
   - other `.github` content: edit it as approved.
3. If ownership or an interface moved, update the counterpart profile too, with the same approval.
4. Log one fragment per proposal:
   - `.github` changes: `python3 .github/scripts/changes.py new-github <proposal#> project-master <slug> --paths "…" --source "#<proposal>"`,
     with the user's approval in `validated-by`;
   - corpus changes: `python3 .github/scripts/changes.py new-context <proposal#> project-master <slug> --paths "…" --source "#<proposal>"`.
5. `python3 .github/scripts/profiles.py check` and `python3 .github/scripts/changes.py check` pass.
6. `/open-pr`, with `Closes #<proposal>` for each applied proposal. The PR needs the `human-change` label.

## 5. Close the loop

- Comment on every proposal with the decision, the reason and the PR link.
- Close rejected proposals as "not planned". Leave needs-info proposals open.
- If ownership or priority changed, update the board.
- Tell the user which agents should restart, or run `/cloud-init refresh`, once the PR is merged.

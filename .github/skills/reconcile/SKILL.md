---
name: reconcile
description: project-master only. Turns a working session (or a branch) into checked fragments, issue progress, board status, corpus and context updates, and a roadmap refresh, starting from the reconcile brief. Use at the end of a session, when another agent delegates its work, or whenever the board may be stale.
---

# /reconcile

**`project-master` runs this.** Any other agent: hand off to project-master instead.

## 0. Brief and snapshot (read only)

```bash
python3 .github/scripts/changes.py brief      # commits, changed paths, rule check, invalid fragments, corpus and .github changes
python3 .github/scripts/ghp.py items --json > "$TMPDIR/board.json"
gh issue list --state all --limit 500 --json number,title,state,stateReason,labels,milestone,updatedAt
gh pr list --state all --limit 200 --json number,title,state,headRefName,isDraft,mergedAt,closingIssuesReferences
```

## 1. Fragments

- Every work change has a fragment in `.changes/unreleased/`, every `.corpus/` change one in `.changes/context/`, and
  every `.github/` change one in `.changes/github/` with the user's approval, all following `.github/templates/`.
  Lint, type and formatting fixes need none. The author writes them with `/log-change`.
  Write a missing one only when its author did not, and set `agent:` to that author.
- Fix invalid fragments (`changes.py check` names the problem).
- No issue for a change? Propose one. Use `roadmap: "unplanned"` until it exists; never invent a link.

## 2. Board and issues: evidence → state

| Evidence | Change |
|---|---|
| Open issue not on the board | `ghp.py add <n> Status=Backlog Priority=… Size=… Area=…` (Priority and Size are [Inference] unless the corpus says) |
| Branch `dev-<n>-*` exists, or the agent commented "started" | `Status=In progress` and a progress comment |
| Open non-draft PR references the issue | `Status=In review` |
| PR merged with `Closes #n`, or the user says done | `Status=Done`. Never close without a merged PR or the user's word |
| `blocked` label, or a comment saying blocked | `Status=Blocked`, and a comment naming the blocker and its owner |
| Fragment `roadmap: "#n"` whose issue is closed or missing | `corpus-drift` or follow-up issue, and ask the user |
| Shipped work with no roadmap item | Note it as scope creep in the report and propose an issue |
| TODO, follow-up or bug found in the session | New issue with acceptance criteria and a corpus ref, or `needs-decision` |

Comments carry the evidence: a PR, commit or fragment link. Batch GitHub writes: more than 5 objects, or any
milestone or field change, needs the user's approval of the list first.

## 3. Corpus and profiles

- An [Open] question was answered, or the corpus was contradicted: propose the corpus edit (in `.corpus/`) and update or
  close the decision issue. Architectural changes go to `cloud-architect` first. Corpus edits get a `.changes/context/` fragment.
- The corpus changed, a milestone moved, a decision was made or breaking fragments landed: the repository profile's
  project status is stale. Run `/cloud-init instructions` (it asks the user before writing) and list the agents that
  should run `/cloud-init refresh`, with the corpus files that changed for each.
- `.github` changes found without an approved fragment: ask the user to validate them, then log them, or revert them.
- Open `scope-proposal` issues: run `/review-proposals`, or list them as pending.

## 4. Roadmap

Regenerate `ROADMAP.md` from the project when statuses, iterations or milestones moved: each milestone with its
goal, done/total, items in progress, blocked items and what's next.

## 5. Close

Put file edits on a `dev-<issue>-reconcile-<date>` branch from `dev`. Run `/log-change`, then `changes.py check`,
then `/open-pr`. GitHub-only updates need no branch. Report in project-master's reconcile output format.

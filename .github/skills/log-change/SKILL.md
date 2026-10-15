---
name: log-change
description: Log the change you just made in .changes/, from the templates - work in .changes/unreleased/, corpus changes in .changes/context/, .github changes in .changes/github/ with the user's explicit approval. Lint, type and formatting fixes need no fragment. Use after each logical change, and whenever the stop hook asks. All agents, project-master included.
---

# /log-change

Every change is logged while you work, from the templates in `.github/templates/`. The stop hook and CI run
`python3 .github/scripts/changes.py check` and refuse missing or off-template fragments.

| What changed | Folder | Template | Create with |
|---|---|---|---|
| anything outside `.corpus/` and `.github/` (code, IaC, docs, tests…) | `.changes/unreleased/` | `fragment.md` | `changes.py new <n> <agent> <slug> --type <type> [--breaking]` |
| `.corpus/` | `.changes/context/` | `context-change.md` | `changes.py new-context <n> <agent> <slug> --paths "…" --source "…"` |
| `.github/` (agent files, instructions, skills, templates, workflows, project files) | `.changes/github/` | `github-change.md` | `changes.py new-github <n> <agent> <slug> --paths "…" --source "…"` |

**No fragment for lint, type and formatting fixes.** Commit them on their own, with a `[CLEAN]` subject
(`[CLEAN] Format with ruff (#42)`). The check ignores files changed only by `[CLEAN]` commits and uncommitted
whitespace-only edits. Don't mix a style fix and a real change in one commit.

1. **Issue number.** It comes from the branch `dev-<issue>-<slug>`, or from the calling skill. With no issue, use
   `unplanned` and say so in the PR. Never guess a number.
2. **Facts, not memory.** `git status --short`, `git diff --stat`, `git log --oneline $(git merge-base HEAD origin/dev)..HEAD`.
3. **One fragment per logical change**: a decision, a feature slice, a migration, a corpus answer. Not one per commit.
   Update your existing fragment as the change evolves (`changes.py list --issue <n>`).
4. **Fill in every placeholder.**
   - Work fragments: the first paragraph is the user-facing `CHANGELOG.md` line, in the past tense. `## Details` holds
     Files, Why (corpus ref, ADR or issue), Verified (the tests you ran; don't list lint or format runs), Rollback and Follow-ups.
   - Corpus fragments: what changed and why, before → after, evidence, agents affected.
   - `.github` fragments: `validated-by` records the user's explicit approval: who, when, and what they approved, such as
     `user, 2026-10-15 14:05: "yes, apply the devops profile"`. Ask before you change the files, not after.
     Without it the check fails.
   - Never put secrets, real project IDs or personal data in a fragment.
5. **Validate and stage.** Run `python3 .github/scripts/changes.py check`, then `git add` the fragment with the work it
   describes. Commit subjects follow `[TYPE](SCOPE) MESSAGE (#<n>)` (see `.github/copilot-instructions.md`).

Never edit another agent's fragment. If it is wrong, comment on the issue; project-master fixes it during reconcile.
Corpus and `.github` fragments are a permanent log: they are never compiled or moved.

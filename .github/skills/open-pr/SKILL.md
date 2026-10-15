---
name: open-pr
description: Open or update the pull request for the current branch from .github/templates/pr-body.md, synthesizing the description from the fragments (work, corpus and .github) of every issue the branch covers. Use when work on an issue is ready for review. All agents.
---

# /open-pr

1. **Preconditions.** You are on a `dev-<issue>-<slug>` branch (or `hotfix`), not on `main` or `dev`. The working tree is clean (commit first). `python3 .github/scripts/changes.py check`
   passes. Relevant tests, lint or `terraform validate`/`plan` were run. If something fails, say so in the PR rather than hiding it.
2. **Covered issues.** `python3 .github/scripts/changes.py issues` reads the issue numbers from the branch name and commit messages.
3. **Read** `python3 .github/scripts/changes.py show --issue <n>` for each issue: all agents' work and context
   fragments (work, corpus and `.github`). Read the acceptance criteria too (`gh issue view <n>`).
4. **Synthesize, don't paste.** Fill `.github/templates/pr-body.md` for a reviewer who has not followed the work:
   - one `### #n` section per issue;
   - corpus changes listed separately;
   - **`.github` changes**: each `.github` fragment with its `validated-by` approval. If there are any, ask the user to
     add the `human-change` label after reviewing them; write "None" otherwise;
   - decisions, verification, rollback and follow-ups;
   - the list of fragments.

   Use `Closes` only when all of an issue's acceptance criteria are met, otherwise `Refs`. Put breaking fragments
   at the top of the Summary.
5. **Create or update.** Put the body file in a temp dir outside the repo.
   - New PR: `git push -u origin HEAD`, then `gh pr create --base dev --title "[TYPE](SCOPE) <summary> (#<n>)" --body-file <tmp>`
     (`--base main` only for `hotfix`)
     (add `--draft` while checks are still running).
   - Existing PR: `gh pr edit --body-file <tmp>`.
6. **Notify.** Comment on each covered issue: `gh issue comment <n> --body "PR: <url> — ready for review"`.
   project-master updates the board from that evidence.
7. Return the PR URL. A maintainer merges (usually squash).

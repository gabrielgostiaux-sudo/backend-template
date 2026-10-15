---
name: init
description: project-master only. Initialises or refreshes the whole team after /project-bootstrap - runs cloud-init for the repository profile and every agent, writes each approved profile directly into its file, logs the changes in .changes/github/ and opens one PR. Use right after bootstrap and whenever the corpus changes materially.
argument-hint: "[all|refresh]"
---

# /init: make the whole team project-aware

**`project-master` runs this.** Any other agent: stop, say so, and suggest a handoff to project-master.

`/init` orchestrates. The per-profile work is done by the `cloud-init` skill (`.github/skills/cloud-init/SKILL.md`),
which writes each profile into the PROFILE block of its file once the user approves it.

## 0. Preflight (read only)

1. `.github/project/manifest.yml` exists. If not, stop: run `/project-bootstrap` first, or say that bootstrap is pending.
2. `python3 .github/scripts/profiles.py list` shows each profile's status.
3. Argument `refresh` (or all profiles already `ready`): only the roles affected, as in cloud-init's refresh mode.
   Default `all`: all six (the repository profile and the five agents).
4. Branch: `git switch -c dev-<issue>-init` from up-to-date `dev`. Use the bootstrap tracking issue, or create one
   (`[project-master] Initialise agent profiles`, label `type:chore`). Fragments and the PR need an issue.

## 1. Draft every profile

Order: `instructions`, `project-master`, `architect`, `data`, `devops`, `security`. For each role, follow cloud-init
steps 1 to 5 up to and including the draft, but don't write yet. Collect every role's GAPS and CONFLICTS for the report;
don't answer them yourself.

## 2. One approval, then write

1. Show the user all six drafts together: for each one a short summary (READ FIRST, GAPS, CONFLICTS) and the full text
   on request. Ask for explicit approval, per profile or for all of them. Apply any corrections the user asks for.
2. Write each approved profile: `python3 .github/scripts/profiles.py set <key> <body-file>`. Leave unapproved ones as they are.
3. `python3 .github/scripts/profiles.py check` passes.

## 3. Log and ship

1. One fragment for the run:
   `python3 .github/scripts/changes.py new-github <issue> project-master init --paths "<every file written>" --source /init`.
   Fill it in from `.github/templates/github-change.md`, with the user's approval in `validated-by`.
2. `python3 .github/scripts/changes.py check` passes.
3. `/open-pr`. The PR needs the `human-change` label, which the user applies after reviewing it.
4. Report:
   - the profiles written, and those not approved;
   - the corpus path;
   - the GAPS questions, numbered with the most important first;
   - corpus files without an `agents:` flag, with a suggested flag;
   - conflicts.

   Remind the user to restart open agent sessions once the PR is merged. Offer to create `needs-decision` issues for
   GAPS not yet tracked; creating more than 5 objects needs approval.

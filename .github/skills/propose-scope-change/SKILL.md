---
name: propose-scope-change
description: Propose a change to your own profile, the repository profile, the corpus, or anything else under .github/, by filing a scope-proposal issue from .github/templates/scope-proposal.md. project-master reviews it and applies it once the user approves. Use whenever your profile is wrong, missing or outdated. All agents, project-master included.
---

# /propose-scope-change

## 1. Pick the kind

| Kind | Target | Applied by |
|---|---|---|
| `profile` | your profile: the PROFILE block of your agent file | project-master, through `cloud-init`, after the user approves. Facts from the corpus come back on every `cloud-init refresh`: put durable additions in `OWNER NOTES`, and fix wrong facts in the corpus. |
| `instructions` | the repository profile (PROFILE block of `.github/copilot-instructions.md`): commands, architecture, conventions, project status | project-master, after the user approves |
| `corpus` | a file in `.corpus/`: answers to [Open] questions, corrections, `agents:` flags | project-master, with the user |
| `github` | other `.github/` content: agent text outside the markers, skills, templates, hooks, workflows | the user decides; project-master or a human applies it |

Propose changes to **your own** profile, the repository profile, the corpus or `.github/`. If another agent's profile
is wrong, say so in a handoff note or on the issue instead.

## 2. Draft precisely

- Read the current text first. For a profile, that's the PROFILE block of the file.
- For a whole profile, write the complete replacement. Otherwise write a unified diff.
- Keep the template structure (`.github/templates/profile.md`, `instructions-profile.md`) and the size limits
  (agent profile ≤ 6,000 characters, repository profile ≤ 9,000).
- Back every change with evidence: the issue or PR where the gap showed up, fragments, corpus IDs.
- One proposal per coherent change.

## 3. Check for duplicates

`gh issue list --label scope-proposal --state open --search "<target>"`. If one already covers it, comment there instead.

## 4. File it

Copy `.github/templates/scope-proposal.md` to a temp file outside the repo, fill in every placeholder, then:

```bash
gh issue create --title "[scope] <target>: <summary>" --body-file <tmp> --label scope-proposal
```

## 5. Record and carry on

Add the proposal link under **Follow-ups** in your current fragment (`/log-change`). Keep working with today's
profile, tagging anything that depends on the proposal [Inference]. If the issue truly can't proceed, comment on
it that it is blocked by the proposal.

---
name: cloud-init
description: First-use setup and refresh for the cloud agents, project-master and the repository profile in copilot-instructions.md. Reads the project corpus files relevant to the role, inspects the repository, and writes the project profile into the agent's own file once the user approves it. Use on first use of an agent, or when the corpus changed. Profiles are written by project-master; any other agent runs it in draft mode.
argument-hint: "[architect|data|devops|security|project-master|instructions|all|refresh] [--draft]"
---

# cloud-init: adapt an agent to this project

Purpose: the cloud agents and project-master are generic and reusable. This skill makes one (or all) of them project-aware by filling the block between `<!-- PROFILE:START -->` and `<!-- PROFILE:END -->` in its agent file. The `instructions` role does the same for the repository profile at the end of `.github/copilot-instructions.md`, which every agent reads. It never changes anything outside those markers.

Role keys and files:

| Key | File | Template |
|---|---|---|
| `architect` | `.github/agents/cloud-architect.agent.md` | `.github/templates/profile.md` |
| `data` | `.github/agents/cloud-data-engineer.agent.md` | `.github/templates/profile.md` |
| `devops` | `.github/agents/cloud-devops-engineer.agent.md` | `.github/templates/profile.md` |
| `security` | `.github/agents/cloud-security-engineer.agent.md` | `.github/templates/profile.md` |
| `project-master` | `.github/agents/project-master.agent.md` | `.github/templates/profile.md` |
| `instructions` | `.github/copilot-instructions.md` (repository profile) | `.github/templates/instructions-profile.md` |

Argument: a role key = initialise that role; `all` = the six in turn; `refresh` = re-run for every role whose profile is `ready`. No argument: use the role of the agent that invoked you; if unknown, ask once.

## Who writes
- **project-master** (directly, or through `/init`) runs the full procedure. Every profile is a change under `.github/`, so it is written only after the user explicitly approves it, and logged in `.changes/github/`.
- **Any other agent**, or `--draft`: run steps 1 to 4, prepare the step 5 profile, and stop before writing. Show the draft, work from it tagged [Inference], and file it with `/propose-scope-change` (kind `profile`) if the user wants it applied.
- Facts that come from the corpus are regenerated on every refresh. A durable correction belongs in the corpus (proposal kind `corpus`), or in `OWNER NOTES`, which refresh preserves.

## Procedure

### 1. Locate things (read only)
- File(s) from the table above. If missing, stop and tell the user where the template is.
- Use the corpus path in the existing profile when it exists. Otherwise use `.corpus/` if present (the team's default corpus path); otherwise look for `docs/corpus/`, `corpus/`, `docs/`, then any folder holding a file named `00_*index*` or `00_README*`. If several candidates or none, ask the user for the path. Do not guess.

### 2. Select the corpus files for the role
- Read `00_*` first. For `project-master`, read every corpus file: project-master owns the corpus and needs its full picture to plan and reconcile work. This ownership does not make it a content-consumer flag and does not require adding `project-master` to `agents:` lists. For `instructions`, read the files flagged `all` plus those describing stack, architecture, conventions and milestones: the repository facts come from step 4, and the corpus says where the target differs and what the current milestone is.
- For the four cloud roles, every corpus file should declare relevance in its YAML front matter (`agents: [architect, data, devops, security]`) or, for `.mmd` files, in a `%% agents: ...` comment line. Select files whose list contains the role key or `all`.
- A file without the flag: classify it from its title and headings, mark it `[Inference]` in the manifest, and list it in the report so the owner can add the flag. Do not edit corpus files.
- Read every selected file fully. Skip files not selected, except to note their names in the manifest as "not flagged".

### 3. Extract what the role needs
Capture facts with their source (`file section/ID`), and tag each as [Decided], [Inference], [Unverified] or [Open] as the corpus does.

| Role | Extract |
|---|---|
| architect | purpose and users; scope and non-goals; constraints (budget, team, skills, regulation, handover); quality-attribute targets and which are missing; decisions (IDs) and their status; topology and external dependencies; known risks; open decisions |
| data | engine and tier; entities, volumes, growth; data classes (personal, operational, media); retention and deletion rules; backup/recovery targets (RPO/RTO) and which are missing; migration tool and conventions; access patterns; storage layout; who may read or write what |
| devops | runtime and deploy targets; environments; IaC tool, folder and state; CI/CD system and stages; scheduled jobs and identities; configuration and environment variables; observability and alerting; budget and cost caps; release and rollback expectations |
| security | what is protected; personal data (yes/no, what kind); actors and roles; trust boundaries and public endpoints; authentication method (decided or open); service accounts and permissions; secrets; external APIs and abuse/cost exposure; retention and deletion duties; regulation mentioned |
| project-master | goals, scope and phases; capabilities, business rules and use cases with IDs; decisions and status; acceptance scenarios; [Open] gaps, [Unverified] facts, conflicts; repository state and delivery implications |
| instructions | from the repository first (step 4): package manager and runtime version, install, test (full and single), lint, format, type-check, pre-commit/pre-push hooks, IaC and container validation; source layout and layers; what exists vs placeholders; local and production deployment paths and their current state; code and test locations, language version, line length, linter rule groups, test discovery, type-checking scope, package names and rename checklist. From the corpus and the GitHub project (`.github/project/`): current and next milestone, active and open decisions, recent breaking changes, definition of done, where the target differs from the current state |

### 4. Inspect the repository (read only)
Record only facts you saw, with paths: languages and package manager; IaC folders and tool/versions; CI files; Dockerfile(s); migrations folder and tool; test and lint commands; existing ADRs/docs/runbooks; `CODEOWNERS`; existing Copilot instructions. For `instructions`, every command must be one you saw defined in the repository. If a corpus statement and the repository disagree, list it under conflicts. Never read, print or copy secrets, `.env` files, state files or credentials.

### 5. Write the profile
Prepare the new profile with the structure of the role's template (Markdown, at most **6,000 characters** for an agent and 9,000 for `instructions`; summarise and point to files, do not paste them). Keep every key, in that order.

Rules: keep `OWNER NOTES` unchanged on refresh; remove nothing the owner added; replace stale facts; never include secrets or real project identifiers beyond what the corpus itself already contains.

Then:
1. **Ask the user.** Show the proposed profile (or, on refresh, what changes) and ask for explicit approval. Do not write anything without a clear yes. Do not bypass CODEOWNERS or the repository checks.
2. **Write it** into the file's PROFILE block: put the body in a temp file outside the repository, then run `python3 .github/scripts/profiles.py set <key> <body-file>`. The tool replaces only the text between the markers and refuses to drop `OWNER NOTES`.
3. **Log it** in one fragment for all the profiles written together: `python3 .github/scripts/changes.py new-github <issue|unplanned> project-master <slug> --paths "<files>" --source cloud-init`. Fill it in from `.github/templates/github-change.md`, and put the user's approval in `validated-by` (who, when, and what they approved).

### 6. Verify
- `python3 .github/scripts/profiles.py check`: one PROFILE block per file, every template key present, size within the limit, front matter intact.
- Check that every file under `READ FIRST` exists.
- `python3 .github/scripts/changes.py check` passes.

### 7. Report to the user (short)
1. Which agent(s) were initialised and the corpus path. 2. The files each will read. 3. The GAPS list as numbered questions (most important first). 4. Corpus files lacking an `agents:` flag or flagged oddly, with a suggested flag. For project-master, report ownership separately from consumer flags; do not suggest adding it to every `agents:` list just because it owns the corpus. 5. Conflicts. 6. When to run `/cloud-init refresh` (whenever a manifest file's `updated` date changes or a file is added or removed). 7. Open agent sessions must restart to see the new profile.

## Refresh mode
Compare the stored MANIFEST with the corpus: new, removed or newer files. For project-master, changes to any corpus file are relevant; for cloud roles, use their flagged files; for `instructions`, also changes to the build, test or lint configuration and to the current milestone. If nothing changed for the selected roles, say so and stop. Otherwise redo steps 2 to 6 for the affected roles and tell the user what changed in the profile (added, removed, changed facts) before asking for approval.

## Do not
Edit corpus files; edit anything outside the PROFILE markers; write a profile without the user's explicit approval and a `.changes/github/` fragment; write a profile from any agent other than project-master; run any command that changes infrastructure or data; invent targets or decisions the corpus does not contain; paste large corpus passages into the profile.

---
name: project-bootstrap
description: Draft a corpus-based GitHub project bootstrap plan and approved-action sequence when project-master finds no manifest or the user explicitly requests bootstrap. Does not perform changes before approval.
argument-hint: "[bootstrap request or project context]"
---

# Project bootstrap planning workflow

## Purpose and trigger

Use this skill only when project-master is initializing and `.github/project/manifest.yml` is missing, or when the user explicitly requests a project bootstrap. Do not invoke it for reconciliation, release, roadmap review, or another narrower task. This skill prepares a complete draft plan and an ordered action sequence; it is an instruction workflow, not a separately running agent and not authorization to execute changes.

## Inputs

- Project-master profile and owner-provided constraints.
- The complete corpus directory from the profile, including all files regardless of `agents:` front matter.
- Current repository state and any project files already present, especially `.github/project/plan.yml`, `manifest.yml`, `SETUP.md`, and `ROADMAP.md`.
- Read-only GitHub project and issue state, if authenticated.
- Explicit user answers about owner, cadence, priorities, dates, or other unresolved planning constraints. Do not infer these as facts.

If the user asks for a narrower task, stop bootstrap planning and report that bootstrap is pending if the manifest is missing.

## Preconditions and evidence

1. If profile `INIT-STATUS` is `pending`, run `/cloud-init project-master` first. If corpus files are missing, new, or newer than the recorded profile, run `/cloud-init refresh` before planning. Do not plan from a stale profile.
2. Check `gh auth status` before relying on GitHub data or proposing an executable GitHub action. The authenticated account must have the required `repo` and `project` scopes. If authentication or scopes are missing, stop GitHub operations and ask the user to authenticate or run `gh auth refresh -s project`; do not ask them to expose a token.
3. Confirm the repository's project owner (user or organization); never guess an owner or silently select a project. Use `gh project list --owner <owner>` for read-only discovery and inspect relevant existing issues/projects. Check the installed `gh` help for commands and options before relying on them; mark unverified command/API behavior `[Unverified]`.
4. Read the whole corpus and repository state. Record goals, scope, phases, capabilities, business rules/use cases and IDs, decisions, open questions, unverified blocking facts, and corpus/repository conflicts. Distinguish evidence tags:
   - `[Decided]`: preserve; do not contradict without asking the user.
   - `[Open]`: keep undecided and draft exactly one decision issue per gap.
   - `[Unverified]`: do not present as fact; draft a time-boxed spike only when the fact blocks work, with corpus update as its output.
   - `[Inference]`: label proposed cadence, sequencing, priorities, or assumptions explicitly.
5. Separate corpus facts from repository evidence. Identify conflicts as drift candidates; never claim planned infrastructure is deployed. Design or architecture choices, data design, delivery design, security design, and code implementation remain with their respective cloud or coding agents. The project-master may plan and track that work, not decide or implement it.

## Draft the plan

Prepare the proposed `.github/project/plan.yml` content and complete action sequence as a draft for project-master to review and present. Do not write files, create GitHub objects, or otherwise cause side effects while drafting. Use the repository's project plan template where available and choose the smallest useful project structure.

Plan only what the corpus and repository evidence support:

- Milestones represent phases or releases with a one-sentence goal. Use 2–4 only when the project warrants them; do not invent due dates.
- Epics group capabilities spanning multiple PRs; issues represent observable, PR-sized work with acceptance criteria citing corpus IDs.
- Create one decision candidate for each `[Open]` gap, labeled `needs-decision`, with the relevant corpus reference and options only when the corpus supports them. Do not assign a person unless the user supplied a GitHub handle; use a role otherwise.
- Create a spike candidate for each blocking `[Unverified]` fact, time-boxed only if duration is grounded or explicitly labeled `[Inference]`.
- Create a drift candidate for each material corpus/repository conflict, labeled `corpus-drift`.
- Propose iterations only with the user's cadence or mark the conventional proposal `[Inference]` (two weeks may be proposed for a volunteer team); do not invent a start date.
- Keep fields proportionate: `Status` (Backlog / Ready / In progress / In review / Done / Blocked), `Priority` (P0–P3), `Size` (XS–XL), `Area` (corpus modules), and text `Corpus ref`. Iteration fields, sub-issue mutations, views, and workflows may require GraphQL or UI steps; mark unverified API behavior and include human setup steps rather than assuming support.
- Use issue types where available; otherwise propose concise labels such as `type:*`, `area:*`, `needs-decision`, `corpus-drift`, `good-first-issue`, and `agent-ready`. Avoid unnecessary ceremony for a small volunteer team.
- Every issue candidate needs acceptance criteria and corpus references, or must be a decision issue. Each issue/action key must be unique and stable (for example, `M1`, `EPIC-01`, `ISS-001`, `DEC-Q1`, `SPIKE-01`, `DRIFT-01`).
- Include a draft `SETUP.md` action list for views/workflows or other UI-only steps that cannot reliably be performed through the API. Include roadmap/context generation actions only where repository state and approved scope warrant them.

For each proposed GitHub object, include its `pm-key` marker and expected manifest record. The draft action sequence must state the read-before-create lookup used to prevent duplicates. Show any assumptions as `[Inference]`, unresolved matters as questions, and unverified commands/API behavior as `[Unverified]`.

## Approval boundary

Project-master reviews the draft for corpus traceability, scope, duplicate candidates, unverified API behavior, and proportionate workload, then presents it to the user. The presentation includes:

- A concise project summary and counts by object type (milestones, epics, issues, decisions, spikes, drift, iterations, fields, labels).
- The proposed first two iterations, if dates/cadence are supported or explicitly marked `[Inference]`.
- Decision questions, blocking spikes, repository drift, and all assumptions.
- The complete proposed action sequence, including repository-owned file changes and GitHub writes.
- Exact commands for the first item of each proposed GitHub object kind, after checking available `gh` help.

**Stop and wait for explicit user approval.** Silence, a request to draft, or approval of this skill/refactor is not approval to bootstrap. No file edits, GitHub writes, project creation, field or milestone changes, or other side effects are allowed before approval of the presented bootstrap plan. Project-master-owned file edits still require the applicable approval prompt. Any GitHub batch of more than five writes, and any milestone or field change, requires explicit approval of the plan before execution. If the user narrows or changes scope, revise and present the affected plan again.

## Apply only approved actions

After explicit approval, execute only the approved plan, safely and idempotently:

1. Recheck authentication, scopes, project owner, and current repository/GitHub state. If state changed since drafting, stop and present the delta for approval.
2. Search for each stable `pm-key` in the relevant existing issues/project state and consult `.github/project/manifest.yml` before creating or adding anything. Reuse matching objects; do not duplicate them. Never delete objects.
3. Apply in dependency order: labels; milestones; project and fields; epics; issues and sub-issues (use task-list links if sub-issue API is unavailable); then add project items and set approved fields.
4. For each created/reused object, record its key, number, and node ID when available in `manifest.yml`. Keep the approved desired state in `plan.yml`. Do not put secrets, tokens, real project IDs, or personal/minor data in files or issues.
5. Copy  .github/templates/check_project.template.json  to  .github/project/check_project.json  and fill it using the selected project and verified created/reused objects. Record the pre-bootstrap items and observed statuses under preserved_items . Do not leave template placeholders in the filled file
6. Write `SETUP.md` for API/UI-only steps. Generate or update `ROADMAP.md` and approved generated context/stamp artifacts only when included in the approved plan. Never edit hooks, workflow lock files, Copilot settings, PROFILE or GENERATED blocks outside their designated ownership, or other human-owned sections.
7. For any API operation not verified by local `gh` help, test only through an approved action; if it fails or cannot be safely confirmed, stop that operation and document the manual setup step instead. Do not improvise mutations.
8. Every file written under `.github/project/` (plan, manifest, check config, setup notes) is a `.github` change. The user's approval of the bootstrap plan covers them: log them in one fragment with `python3 .github/scripts/changes.py new-github <bootstrap-issue|unplanned> project-master bootstrap --paths ".github/project/" --source /project-bootstrap`, filled in from `.github/templates/github-change.md`, with that approval in `validated-by`.

## Verify and report

After applying approved work, verify read-only that:

- Each approved `pm-key` resolves to exactly one object and manifest entries agree with the corresponding issue numbers/node IDs.
- The project, milestones, issues, parent/child links, and fields reflect only the approved plan.
- No unapproved objects or duplicate records were created.
- `plan.yml`, `manifest.yml`, `SETUP.md`, and generated roadmap/context agree with the verified project state, where those files were approved.
- Run  uv run python .github/skills/project-bootstrap/check_project_once.py .github/project/check_project.json . This is a read-only check. Resolve failures or report them; do not treat a failed or incomplete check as successful verification. The script checks up to 1,000 issues and project items; if the repository/project exceeds that limit, extend pagination before relying on the result.

Report concise results: applied versus reused object counts, files changed, verification performed, UI/manual steps outstanding, any failed or unverified actions, and items that still need a decision or approval. Link to GitHub objects and repository paths; do not claim an action succeeded without verification.

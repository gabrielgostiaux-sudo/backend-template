# Repository instructions

## Team rules (every agent, project-master included)

1. **Changes under `.github/` need the user's explicit approval.** This covers agent files, these instructions,
   skills, templates, hooks and workflows. Before you change anything there, describe the change, ask the user,
   and wait for a clear yes. Record that approval in the `validated-by` field of a `.changes/github/` fragment.
   The pull request also needs the `human-change` label, which only a human applies.
2. **Log every change in `.changes/`** with `/log-change`, while you work:
   - work (code, IaC, docs, tests…) → `.changes/unreleased/<issue>-<agent>-<slug>.md`
   - corpus changes (`.corpus/`) → `.changes/context/<issue>-<agent>-<slug>.md`
   - `.github/` changes → `.changes/github/<issue>-<agent>-<slug>.md`, with the user's approval

   Lint, type and formatting fixes need no fragment: commit them on their own as `[CLEAN]`.
   A hook reminds you once before you finish if something is not logged; CI runs the same check on every PR.
3. **Use the templates in `.github/templates/`** for fragments, profiles, PR bodies and proposals. Fragments that
   don't follow their template fail the check.

## Before any task

- Read your agent profile (the PROFILE block in your own agent file) and the repository profile at the end of this
  file: commands, architecture, conventions and the current project status.
- The corpus in `.corpus/` is the source of truth for what the project must become. GitHub is the source of
  status. The repository profile describes the repository as it is today. Cite corpus files and IDs, and use the
  tags [Decided], [Inference], [Unverified] and [Open]. When the corpus and the repository disagree, say so;
  don't silently pick one.

## Roles

| Agent | Looks after |
|---|---|
| `project-master` | GitHub project and issues, roadmap, corpus (`.corpus/`), project files (`.github/project/`), all profiles, changelog compilation |
| `cloud-architect` | architecture, quality attributes, ADRs, cost model |
| `cloud-data-engineer` | schema, migrations, backup/recovery, retention, data runbooks |
| `cloud-devops-engineer` | IaC, CI/CD, environments, observability, release safety |
| `cloud-security-engineer` | threat model, identities, secrets, exposure, data protection |
| default agent and humans | application code |

The board, issue fields, milestones, labels, the roadmap, the corpus and the profiles are changed by
`project-master`. Other agents comment on issues, open PRs, hand off to project-master, or run `/propose-scope-change`.
At the end of a session, hand off to `project-master` (`/reconcile`).

## Git and GitHub workflow

- Follow the team Git flow with `main` in place of `master`: `main` is the release branch, `dev` collects work for the next release, and `hotfix` carries urgent production fixes. Avoid adding other long-lived branches.
- Work one issue at a time. Create feature branches from an up-to-date `dev`, named `dev-<issue>-<slug>` (for example `dev-42-order-api`); the issue number in the name links the branch to its changelog fragments. Merge completed, reviewed feature work into `dev`. Merge `dev` to `main` for a planned release, and merge `hotfix` to `main` for production fixes. Do not commit directly to `main` or `dev` outside initial setup or release tagging.
- Keep commits focused on one coherent change. Stage only related files (or selected hunks with `git add -p`); avoid staging the entire working tree blindly. Check `git status` first and preserve unrelated user changes. Stage the change log fragment together with the work it describes.
- Use commit subjects in `[TYPE](SCOPE) MESSAGE` form, with optional scope, imperative wording, and no trailing punctuation; end with the issue reference when there is one. Types from the team Git guide: `BF` bug fix, `FE` feature, `ENH` refactor/improvement/security enhancement, `CLEAN` formatting or cleanup, `DOC` documentation, `CONFIG` configuration/dependency, `TEST` tests, and `M` major repository changes. Example: `[DOC] Document GitHub workflow (#42)`.
- Commit complete, related changes in small steps. Push the intended branch explicitly and open pull requests into `dev` with `/open-pr`, which builds the description from `.github/templates/pr-body.md` and the issue's fragments; a maintainer handles release/hotfix merges into `main`. Feature-branch changes are typically squash-merged, while release merges can preserve the macro history; follow repository settings and maintainer direction.
- Use `gh` for GitHub platform operations such as inspecting pull requests and issues or creating a pull request; use `git` for local repository and branch operations. Confirm the current branch and target before publishing or merging, and do not merge a pull request unless asked or clearly authorized.
- Tag releases on `main`; do not create or push release tags until the relevant CI checks pass and a release is authorized. At release, project-master compiles `.changes/unreleased/` into `CHANGELOG.md`.
- Avoid rebasing in this Git-flow workflow. Do not amend or rewrite commits that have already been published; the team guide permits amending a local, unpushed commit when correcting its message or adding a missed file.
- Dependabot (`.github/dependabot.yml`) opens weekly update PRs for GitHub Actions and `uv`. They are exempt from the change log check; review and merge them like any other PR.
- Lint, type and formatting fixes go in their own `[CLEAN]` commits, so they need no changelog fragment. Don't exclude files or folders from the linters to make errors disappear; fix them or ask.

## Repository profile (managed by the `cloud-init` skill)

Written between the markers below by `project-master` through `/cloud-init instructions` (or `/init`), after the user
approves it. It holds this repository's build and test commands, architecture, code and test conventions, and the
current project status. Everything outside the markers is generic and reusable across projects.

<!-- PROFILE:START -->
INIT-STATUS: pending
<!-- PROFILE:END -->

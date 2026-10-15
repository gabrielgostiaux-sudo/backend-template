# Agent team for GitHub Copilot: setup and operating guide

Five Copilot custom agents: **project-master** plus four reusable cloud specialists (**cloud-architect**,
**cloud-data-engineer**, **cloud-devops-engineer**, **cloud-security-engineer**). Every agent follows the same three rules:

1. **Changes under `.github/` need your explicit approval.** The agent asks you first, records your answer in a log
   entry, and the PR needs your `human-change` label.
2. **Every change is logged in `.changes/`.** Lint, type and formatting fixes are the exception: they are committed
   as `[CLEAN]` and need no entry.
3. **Templates in `.github/templates/` are used for everything they cover.**

Nothing blocks the agents while they work. One hook reminds them to log before they finish, and the CI check plus
your review are the real gate.

## Layout

```
.corpus/                           the project corpus: source of truth (README: 00_index, agents: flags, IDs, tags)
.changes/
  unreleased/                      work log: <issue>-<agent>-<slug>.md → CHANGELOG.md at release
  context/                         corpus change log (permanent)
  github/                          .github change log, each entry with your approval in validated-by (permanent)
  released/<version>/              compiled work entries
.github/
  copilot-instructions.md          generic team rules, roles, Git flow + repository PROFILE block
  agents/                          5 agents: generic text + a PROFILE block written by cloud-init
  project/                         plan.yml, manifest.yml, check_project.json, SETUP.md (/project-bootstrap)
  skills/
    project-bootstrap/             corpus → GitHub project, files in .github/project/ (+ check_project_once.py)
    cloud-init/                    builds a profile from the corpus and the repo, writes it after your approval
    init/                          project-master: cloud-init for the repository profile and all five agents
    reconcile/                     project-master: brief → log entries, issues, board, corpus, profiles, roadmap
    review-proposals/              project-master: decide proposals with you, then apply them
    propose-scope-change/          everyone: scope-proposal issue
    log-change/                    everyone: log entry in .changes/
    open-pr/                       everyone: PR description from the log entries
  templates/                       fragment, context-change, github-change, profile, instructions-profile,
                                   pr-body, scope-proposal, check_project.template.json
  hooks/hooks.json                 one hook: agentStop → require_changelog.py
  scripts/                         changes.py (log entries and the check), profiles.py (PROFILE blocks), ghp.py (board)
  workflows/ci.yml                 your CI: uv lock check, uv sync, prek hooks, Terraform when present
  workflows/changes-check.yml      .github label check, change log check, profile check
  dependabot.yml                   weekly updates for GitHub Actions and uv
  CODEOWNERS, ISSUE_TEMPLATE/scope-proposal.yml, pull_request_template.md
```

## The one hook

`agentStop` runs `require_changelog.py` when an agent is about to finish its turn. It runs `changes.py check`, and if
something is not logged, or a log entry doesn't follow its template, it asks the agent once to fix that, then lets it
stop. It never stops a command from running.

What the check expects:

| Changed files | Log entry needed | Template |
|---|---|---|
| anything except `.corpus/`, `.github/`, `.changes/` | `.changes/unreleased/<issue>-…md` (named after the branch's issue) | `fragment.md` |
| `.corpus/…` | `.changes/context/…md` | `context-change.md` |
| `.github/…` | `.changes/github/…md`, with `validated-by` filled in with your approval | `github-change.md` |
| files changed only by `[CLEAN]` commits, or whitespace-only edits | none | — |
| `ROADMAP.md`, `CHANGELOG.md`, `changelog.json` (generated) | none | — |

## Checks and branch protection

| Workflow | Job (check name) | Runs on | What fails it |
|---|---|---|---|
| `ci.yml` | `checks` | every PR; pushes to `main`, `dev`, `hotfix` | stale `uv.lock`, a failed `uv sync`, any prek pre-commit or pre-push hook |
| `changes-check.yml` | `changes` | every PR, and when a label is added or removed | `.github/` changed without the `human-change` label; a change without a log entry; an entry off-template; a `.github` entry without your approval; a malformed profile |

Dependabot PRs run `checks` normally. The `changes` job is skipped by its `if:` condition, and GitHub reports a job
skipped that way as Success, so it doesn't block the merge. Neither workflow uses `paths:` or `branches:` filters on
`pull_request`. A workflow skipped by a filter leaves its required check Pending forever, so keep it that way.

**Set it up** (Settings → Rulesets → New ruleset → New branch ruleset):
1. Target branches: `main` and `dev`, typed exactly, without `*` (feature branches like `dev-12-x` stay free).
   Enforcement: Active.
2. Tick **Require a pull request before merging**, then **Require review from Code Owners**.
3. Tick **Require status checks to pass** and add `checks` and `changes`.
4. Optionally tick **Block force pushes**.

### Learn more (GitHub Docs)
- [Status checks](https://docs.github.com/en/pull-requests/reference/status-checks)
- [Troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)
- [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) · [Creating rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository) · [Available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Using conditions to control job execution](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions) · [Workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)

## Prerequisites

- Copilot CLI (or the cloud agent), Python 3, git, `uv`, and `gh` with `gh auth refresh -s project`.
- Copy the kit into the repository root. Replace the handle in `.github/CODEOWNERS`. Commit and push to `main`, and
  create `dev` from `main`.
- Create the `human-change` label, then the ruleset above.
- Trust the folder when the CLI asks; repository hooks only run in trusted folders.

## Initialization workflow

1. **Clone the repo.**
2. **Upload the corpus** to `.corpus/`, following its README, and log it:
   `python3 .github/scripts/changes.py new-context unplanned human corpus-upload --paths ".corpus/" --source "initial upload"`.
3. **Bootstrap:** `copilot --agent project-master`, then `/project-bootstrap`. It drafts the plan, waits for your
   approval, creates the GitHub project, writes `.github/project/`, logs it in `.changes/github/` and verifies it.
   Add the `human-change` label to its PR and merge it.
4. **Initialise:** as project-master, run `/init`. It drafts the repository profile and the five agent profiles, shows
   them to you, writes the ones you approve straight into their files, logs them and opens one PR. Review it, add the
   label, merge, and restart open agent sessions.

## Day-to-day loop

| Who | Does |
|---|---|
| any agent | branch `dev-<issue>-<slug>` from `dev` → work → `/log-change` → `[TYPE](SCOPE) … (#n)` commits → `/open-pr` into `dev` |
| any agent, lint/format/type fix | separate `[CLEAN]` commit, no log entry |
| any agent, a `.github` change | asks you first, records your answer in `.changes/github/`, PR gets your label |
| any agent, profile or corpus wrong | `/propose-scope-change` |
| project-master | `/reconcile`, `/review-proposals` (asks you before applying), release, roadmap review |
| you | answer approval questions, review PRs, add `human-change` when `.github/` changed, merge |

## Limits to know

- Nothing technically stops an agent from editing `.github/` or writing "approved" in `validated-by` without asking.
  The `human-change` label, which only you apply, CODEOWNERS review and the ruleset are what guarantee you see every
  `.github` change before it lands.
- `[CLEAN]` is trusted: a substantive change committed as `[CLEAN]` skips the log. Review catches it.
- The hook runs once per turn: an agent that ignores the reminder can still finish. CI then fails the PR.

## What changed in your reference files

- **Cloud agents:**
  - front matter: no hooks; one handoff, "Record in the project" → project-master;
  - the PROFILE block stays in the agent file and is written by `cloud-init` after your approval;
  - rule 1 reads the repository profile too;
  - new rule 8: the team rules.
- **project-master:**
  - owns `.github/project/`, `.corpus/` and all profiles;
  - every `.github` change it makes needs your approval and a `.changes/github/` entry;
  - reconcile starts from `changes.py brief`.
- **cloud-init:**
  - your original procedure, plus the `instructions` role (repository profile);
  - writes with `profiles.py set` after your explicit approval and logs in `.changes/github/`;
  - default corpus path `.corpus/`.
- **project-bootstrap:**
  - two changes: the check template is copied from `.github/templates/`, and a new step 8 logs the
    `.github/project/` files.
- **check_project_once.py and the template's content:** unchanged.

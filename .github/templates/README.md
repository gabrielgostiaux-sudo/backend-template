# Templates

Every agent uses these templates (team rule 3). Changes to them are `.github` changes: they need the user's explicit
approval and a `.changes/github/` fragment.

| Template | Used by | Becomes | Checked by |
|---|---|---|---|
| `fragment.md` | `/log-change`, `changes.py new` | `.changes/unreleased/<issue>-<agent>-<slug>.md` | stop hook and CI (`changes.py check`) |
| `context-change.md` | `/log-change`, `changes.py new-context` | `.changes/context/<issue>-<agent>-<slug>.md` (corpus changes) | stop hook and CI |
| `github-change.md` | `/log-change`, `changes.py new-github` | `.changes/github/<issue>-<agent>-<slug>.md` (`.github` changes, with `validated-by`) | stop hook and CI |
| `profile.md` | `cloud-init`, `/init` | the PROFILE block of each agent file | `profiles.py check` |
| `instructions-profile.md` | `cloud-init instructions`, `/init` | the PROFILE block of `copilot-instructions.md` | `profiles.py check` |
| `pr-body.md` | `/open-pr` | PR descriptions | review |
| `scope-proposal.md` | `/propose-scope-change` | `scope-proposal` issue bodies | review |
| `check_project.template.json` | `/project-bootstrap` | `.github/project/check_project.json` | `check_project_once.py` |

Fragment checks are template-driven: a fragment must have every front-matter key and every `##` section of its
template, and no placeholder line (`<…>`) left as is. Changing a template changes what the check expects.

GitHub reads two templates only from fixed locations, so they stay outside this folder:
`.github/pull_request_template.md` (PRs opened in the UI) and `.github/ISSUE_TEMPLATE/scope-proposal.yml`.

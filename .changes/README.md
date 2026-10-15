# Changes

Every change is logged here, by whoever made it (team rule 2), from the templates in `.github/templates/`.

| Folder | What | Template | Lifecycle |
|---|---|---|---|
| `unreleased/` | work: code, IaC, docs, tests… | `fragment.md` | compiled into `CHANGELOG.md` / `changelog.json` at release, then moved to `released/<version>/` |
| `context/` | changes to the corpus (`.corpus/`) | `context-change.md` | permanent log; never compiled or moved |
| `github/` | changes to `.github/`, each with the user's explicit approval in `validated-by` | `github-change.md` | permanent log; never compiled or moved |
| `released/<version>/` | released work fragments | — | written by project-master at release |

Names: `<issue>-<agent>-<slug>.md`, or `unplanned-<agent>-<slug>.md`.

Lint, type and formatting fixes need no fragment: commit them on their own as `[CLEAN]`.

```bash
python3 .github/scripts/changes.py new 42 cloud-devops-engineer canary-deploys --type changed
python3 .github/scripts/changes.py new-context 57 project-master pitr-window --paths ".corpus/07_architecture.md" --source "#57"
python3 .github/scripts/changes.py new-github 61 project-master devops-profile --paths ".github/agents/cloud-devops-engineer.agent.md" --source cloud-init
python3 .github/scripts/changes.py show --issue 42     # the per-issue changelog (all kinds)
python3 .github/scripts/changes.py check               # same check as the stop hook and CI
```

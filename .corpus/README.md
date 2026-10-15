# Corpus

The project's source of truth for every agent. Upload it here (as a human, outside agent sessions) before
project-master runs `/project-bootstrap`. Only project-master and humans change it afterwards.

## Conventions read by `cloud-init` and `/project-bootstrap`

- **`00_index.md` (or `00_README.md`) first.** It lists the files, their order of authority and what each contains.
- **Number the files** so authority and reading order are clear: `01_brief.md`, `02_business-rules.md`,
  `07_architecture.md`, `adr/0001-database.md`. When files disagree, the index says which wins.
- **Declare relevance** in each file's YAML front matter. project-master reads every file regardless.

  ```yaml
  ---
  title: Business rules
  updated: 2026-10-15
  agents: [architect, data, devops, security]   # or [all]
  ---
  ```
  Mermaid `.mmd` files use a comment line: `%% agents: architect, devops`.
- **IDs and tags.** Give requirements, rules and decisions stable IDs (`BR-13`, `DEC-04`, `UC-2`), and tag
  statements [Decided], [Inference], [Unverified] or [Open]. Agents cite `02 BR-13`, and bootstrap creates one
  decision issue per [Open] gap.
- Prefer Markdown or text. PDFs need a text layer. No secrets, real project IDs or personal data.

Every change here, the first upload included, is logged in `.changes/context/` from
`.github/templates/context-change.md`. For the first upload, run
`python3 .github/scripts/changes.py new-context unplanned human corpus-upload --paths ".corpus/" --source "initial upload"`
and fill it in.

After any change here: project-master runs `/cloud-init refresh` (or `/init refresh`), and `/project-bootstrap`
again only if the scope changed. Files starting with `_` are generated helpers.

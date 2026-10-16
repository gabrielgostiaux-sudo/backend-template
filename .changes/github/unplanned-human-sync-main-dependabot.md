---
paths: ".github/workflows/, .github/dependabot.yml"
roadmap: "unplanned"
agent: human
source: "Dependabot PRs merged into main"
validated-by: "Gabriel, 2026-10-16: approved the 3 action bumps and targeting dev"
date: 2026-10-16 10:31
---
Brought the Dependabot action updates from main into dev, and pointed Dependabot at dev.

## Details
- **Before → after:** setup-uv v6 → v7, setup-terraform v3 → v4, setup-tflint v4 → v6; Dependabot PRs targeted main → now target dev
- **Why:** the three Dependabot PRs were merged into main and dev was behind
- **Effect:** CI on dev uses the new action versions; future Dependabot PRs open against dev
INIT-STATUS: ready
INIT-DATE: <YYYY-MM-DD>
ROLE: instructions
CORPUS: <path>
MANIFEST: <file | updated | flagged (yes/inferred/no)>, one per line

### Build, test, and checks
- <package manager and runtime version; lock file rule>
- <install / synchronize dependencies>
- <full test run, and one test run with an example>
- <lint, format check, format apply>
- <type-check>
- <pre-commit and pre-push hooks, and how to run each stage>
- <IaC init and validation, container or compose validation>
(Only commands verified in the repository, with the files that define them.)

### Architecture
- <source layout and each layer or module with its responsibility>
- <what exists today vs placeholders; what agents must not assume exists>
- <local development deployment path and how it starts>
- <production deployment target and its current state vs the corpus; things not to run together>

### Code and test conventions
- <where importable code and each test level live>
- <language version, line length, linters and notable rule groups, test-file exceptions>
- <test discovery and type-checking scope; annotation expectations>
- <distribution and package names, and everything to update together when renaming>

### Project status
- <current milestone: title, goal, due date or [Open]; next milestone>
- <active decisions: DEC/ADR IDs, one line each, [Decided] only>
- <open decisions that block work: issue links>
- <recent breaking changes, from fragments with breaking: true, or "none">
- <definition of done, from the corpus or the team default: tests, fragment, PR from /open-pr>
- <where the repository is behind or differs from the corpus target, with corpus IDs>

OWNER NOTES: <preserve whatever was here before, verbatim>

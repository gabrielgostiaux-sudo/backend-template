#!/usr/bin/env python3
"""Change log of the team: fragments in .changes/, validated against the templates.

Folders (file names: <issue|unplanned>-<agent>-<slug>.md)
  .changes/unreleased/  work: code, IaC, docs...             template fragment.md
  .changes/context/     changes to .corpus/                  template context-change.md
  .changes/github/      changes to .github/, with the user's template github-change.md
                        explicit approval in validated-by
  .changes/released/    compiled work fragments (project-master, at release)

Rules checked by the agentStop hook, by CI and by `check`:
  1. changed files outside .corpus/ and .github/ need a work fragment, named after
     the branch's issue when it has one
  2. changed files in .corpus/ need a context fragment
  3. changed files in .github/ need a github fragment whose validated-by records
     the user's explicit approval
  4. every changed fragment follows its template: same front-matter keys, same
     ## sections, no placeholder left
Not counted as changes:
  - .changes/ itself and generated files (ROADMAP.md, CHANGELOG.md, changelog.json)
  - lint, type and formatting fixes: files changed only by commits whose subject
    starts with [CLEAN], and uncommitted changes that are whitespace-only

Commands
  changes.py new <issue|unplanned> <agent> <slug> [--type T] [--breaking]
  changes.py new-context <issue|unplanned> <agent> <slug> [--paths P] [--source S]
  changes.py new-github <issue|unplanned> <agent> <slug> [--paths P] [--source S]
                        [--validated-by "who, when: what they approved"]
  changes.py list [--issue N] [--kind work|context|github]
  changes.py show --issue N        an issue's changelog (all kinds, oldest first)
  changes.py issues                issues covered by the current branch
  changes.py check [--base REF] [--head REF] [--branch NAME] [--no-worktree]
  changes.py brief                 reconcile brief for project-master
"""

import datetime as dt
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / ".github" / "templates"
DIRS = {
    "work": ".changes/unreleased",
    "context": ".changes/context",
    "github": ".changes/github",
}
TEMPLATE_OF = {
    "work": "fragment.md",
    "context": "context-change.md",
    "github": "github-change.md",
}
TYPES = (
    "added",
    "changed",
    "fixed",
    "removed",
    "deprecated",
    "security",
    "docs",
    "infra",
    "chore",
)
GENERATED = ("roadmap.md", "changelog.md", "changelog.json")
STYLE_COMMIT = "[CLEAN]"
PENDING = "PENDING: ask the user and record their explicit approval"
NAME_RE = re.compile(
    r"^(\d+|unplanned)-([a-z0-9]+(?:-[a-z0-9]+)*?)-([a-z0-9][a-z0-9-]*)\.md$"
)
FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
PLACEHOLDER_RE = re.compile(r"<[^<>\n]{3,}>")


# ---------------------------------------------------------------- git
def git(*args, root=ROOT):
    try:
        r = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def default_base(root=ROOT):
    """Git flow: feature branches start from dev; hotfix and release work from main."""
    branch = git("rev-parse", "--abbrev-ref", "HEAD", root=root)
    dev_refs = ("origin/dev", "dev")
    main_refs = ("origin/main", "main", "origin/HEAD", "origin/master", "master")
    hot = branch.startswith(("hotfix", "main"))
    for ref in (main_refs + dev_refs) if hot else (dev_refs + main_refs):
        b = git("merge-base", "HEAD", ref, root=root)
        if b:
            return b
    return ""


def branch_issue(branch):
    # dev-42-slug (also 42-slug, x/42-slug)
    m = re.match(r"^(?:[\w.-]+/)?(?:dev-)?(\d+)(?:-|$)", branch or "")
    return m.group(1) if m else None


def changed_paths(root, base, head=None, worktree=True):
    out = set()
    if base:
        rng = f"{base}..{head}" if head else base
        out.update(
            p for p in git("diff", "--name-only", rng, root=root).splitlines() if p
        )
    if worktree:
        status = git("status", "--porcelain", "--untracked-files=all", root=root)
        for line in status.splitlines():
            p = line[3:].split(" -> ")[-1].strip().strip('"')
            if p:
                out.add(p)
    return sorted(out)


def style_only(root, path, base, head=None, worktree=True):
    """True when a file's changes are only lint/type/format fixes.

    Committed changes count as style-only when every commit touching the file has a
    [CLEAN] subject; uncommitted changes when they are whitespace-only.
    """
    if base:
        rng = f"{base}..{head}" if head else f"{base}..HEAD"
        subjects = git("log", "--format=%s", rng, "--", path, root=root).splitlines()
        if any(not s.startswith(STYLE_COMMIT) for s in subjects):
            return False
    if worktree:
        if git("ls-files", "--others", "--exclude-standard", "--", path, root=root):
            return False  # new untracked file: real content
        if git("diff", "HEAD", "--", path, root=root):
            ws = git(
                "diff", "HEAD", "-w", "--ignore-blank-lines", "--", path, root=root
            )
            if ws:
                return False
    return True


# ------------------------------------------------------------ templates and fragments
def split(text):
    m = FM_RE.match(text)
    if not m:
        return None, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.split(" #")[0].strip().strip('"').strip("'")
    return meta, m.group(2)


def template(kind):
    text = (TEMPLATES / TEMPLATE_OF[kind]).read_text(encoding="utf-8")
    meta, body = split(text)
    sections = [ln.strip() for ln in body.splitlines() if ln.startswith("## ")]
    placeholders = [ln.strip() for ln in body.splitlines() if PLACEHOLDER_RE.search(ln)]
    return text, list(meta), sections, placeholders


def validate(path, kind):
    """Problems with one fragment, judged against its template."""
    path = pathlib.Path(path)
    name = path.name
    _, keys, sections, placeholders = template(kind)
    problems = []
    if not NAME_RE.match(name):
        problems.append(f"{name}: name must be <issue|unplanned>-<agent>-<slug>.md")
    meta, body = split(path.read_text(encoding="utf-8"))
    if meta is None:
        tpl = TEMPLATE_OF[kind]
        return problems + [
            f"{name}: no front matter (start from .github/templates/{tpl})"
        ]
    missing = [k for k in keys if k not in meta]
    if missing:
        problems.append(
            f"{name}: missing front-matter keys {missing} ({TEMPLATE_OF[kind]})"
        )
    lines = [ln.strip() for ln in body.splitlines()]
    problems += [f"{name}: missing section '{s}'" for s in sections if s not in lines]
    left = [p for p in placeholders if p in lines]
    if left or PLACEHOLDER_RE.search(body.split("## ", 1)[0]):
        problems.append(f"{name}: template placeholders not filled in")
    for k, v in meta.items():
        if re.fullmatch(r"\{\w+\}", v):
            problems.append(f"{name}: front-matter '{k}' not filled in")
    rm = meta.get("roadmap", "")
    if not (re.fullmatch(r"#\d+", rm) or rm == "unplanned"):
        problems.append(f'{name}: roadmap must be "#N" or "unplanned"')
    nm = NAME_RE.match(name)
    if nm and rm and nm.group(1) != rm.lstrip("#"):
        problems.append(f"{name}: file name and roadmap {rm} disagree")
    if kind == "work" and meta.get("type") not in TYPES:
        problems.append(f"{name}: type must be one of {', '.join(TYPES)}")
    if kind == "github":
        v = meta.get("validated-by", "")
        if (
            not v
            or v.upper().startswith("PENDING")
            or v.lower() in ("none", "n/a", "-")
        ):
            problems.append(
                f"{name}: validated-by must record the user's explicit approval "
                "(who, when, what they approved). Ask the user first."
            )
    if not meta.get("agent"):
        problems.append(f"{name}: agent is empty")
    return problems


def fragments(kind, issue=None, root=ROOT):
    d = pathlib.Path(root) / DIRS[kind]
    files = (
        [p for p in sorted(d.glob("*.md")) if p.name != "README.md"]
        if d.exists()
        else []
    )
    if issue:
        files = [p for p in files if p.name.startswith(f"{issue}-")]

    def date(p):
        return (split(p.read_text(encoding="utf-8"))[0] or {}).get("date", "")

    return sorted(files, key=date)


# ---------------------------------------------------------------- the rule check
def classify(path):
    p = path.replace("\\", "/")
    if p.startswith(".changes/") or p.lower() in GENERATED:
        return None
    if "/__pycache__/" in f"/{p}" or p.endswith((".pyc", ".pyo")):
        return None
    if p.startswith(".github/"):
        return "github"
    if p.startswith(".corpus/"):
        return "context"
    return "work"


def short(paths, n=5):
    return ", ".join(paths[:n]) + (" …" if len(paths) > n else "")


def check(root=ROOT, base=None, head=None, branch=None, worktree=True):
    root = pathlib.Path(root)
    base = base if base is not None else default_base(root)
    branch = branch or git("rev-parse", "--abbrev-ref", "HEAD", root=root)
    changed = changed_paths(root, base, head, worktree)
    groups = {"work": [], "context": [], "github": []}
    for p in changed:
        kind = classify(p)
        if kind and not style_only(root, p, base, head, worktree):
            groups[kind].append(p)

    def frags(kind):
        prefix = DIRS[kind] + "/"
        return [
            p
            for p in changed
            if p.startswith(prefix)
            and p.endswith(".md")
            and not p.endswith("README.md")
            and (root / p).exists()
        ]

    problems = []
    work = groups["work"]
    if work:
        issue = branch_issue(branch)
        mine = frags("work")
        if issue:
            mine = [p for p in mine if os.path.basename(p).startswith(f"{issue}-")]
        if not mine:
            where = (
                f"`{DIRS['work']}/{issue}-<agent>-<slug>.md`"
                if issue
                else f"a fragment in `{DIRS['work']}/`"
            )
            problems.append(
                f"{len(work)} changed file(s) ({short(work)}) have no {where}. "
                "Run /log-change (lint, type and formatting fixes need no fragment: "
                f"commit them as {STYLE_COMMIT})."
            )
    if groups["context"] and not frags("context"):
        problems.append(
            f"Corpus changed ({short(groups['context'])}) without a fragment in "
            f"`{DIRS['context']}/`. Run /log-change."
        )
    if groups["github"] and not frags("github"):
        problems.append(
            f".github/ changed ({short(groups['github'])}) without a fragment in "
            f"`{DIRS['github']}/`. Ask the user to approve these changes explicitly, "
            "then run "
            "/log-change and record their approval in validated-by."
        )
    for kind in DIRS:
        for p in frags(kind):
            problems.extend(validate(root / p, kind))
    return problems


# ---------------------------------------------------------------- brief
def brief(root=ROOT):
    base = default_base(root)
    branch = git("rev-parse", "--abbrev-ref", "HEAD", root=root)
    changed = changed_paths(root, base)
    commits = []
    if base:
        commits = git(
            "log", "--oneline", "--no-decorate", f"{base}..HEAD", root=root
        ).splitlines()
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    out = [
        f"## Reconcile brief ({stamp}, branch `{branch}`, since `{base[:9] or 'n/a'}`)",
        f"- Commits ({len(commits)}): " + ("; ".join(commits[:15]) or "none"),
        f"- Changed paths ({len(changed)}): " + (", ".join(changed[:30]) or "none"),
    ]
    corpus = [p for p in changed if p.startswith(".corpus/")]
    if corpus:
        out.append(
            f"- Corpus changed: {short(corpus, 15)} → suggest /cloud-init refresh"
        )
    gh = [p for p in changed if p.startswith(".github/")]
    if gh:
        out.append(
            f"- .github changed: {short(gh, 15)} "
            "(needs the user's validation and label)"
        )
    problems = check(root)
    out.append("- Rule check: " + ("OK" if not problems else "; ".join(problems[:10])))
    invalid = [
        pr for k in DIRS for f in fragments(k, root=root) for pr in validate(f, k)
    ]
    if invalid:
        out.append(
            f"- Invalid fragments anywhere ({len(invalid)}): " + "; ".join(invalid[:8])
        )
    if not (pathlib.Path(root) / ".github" / "project" / "manifest.yml").exists():
        out.append(
            "- Project: not bootstrapped (`.github/project/manifest.yml` missing)"
        )
    out.append(
        "- Open scope proposals: `gh issue list --label scope-proposal --state open`"
    )
    return "\n".join(out)


# ---------------------------------------------------------------- cli
def opt(a, name, default=None):
    if name in a and a.index(name) + 1 < len(a):
        return a[a.index(name) + 1]
    return default


def create(kind, issue, agent, slug, values):
    slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
    d = ROOT / DIRS[kind]
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{issue}-{agent}-{slug}.md"
    if path.exists():
        sys.exit(f"exists: {path.relative_to(ROOT)} (update it instead)")
    values.update(
        roadmap="unplanned" if issue == "unplanned" else f"#{issue}",
        agent=agent,
        date=dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    path.write_text(template(kind)[0].format(**values), encoding="utf-8")
    print(path.relative_to(ROOT))


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd = a[0]
    if "-h" in a or "--help" in a:
        sys.exit(__doc__)
    if cmd in ("new", "new-context", "new-github") and len(a) < 4:
        sys.exit(f"usage: changes.py {cmd} <issue|unplanned> <agent> <slug> [options]")
    if cmd == "new":
        t = opt(a, "--type", "changed")
        if t not in TYPES:
            sys.exit(f"--type must be one of {TYPES}")
        breaking = "true" if "--breaking" in a else "false"
        create("work", a[1], a[2], a[3], {"type": t, "breaking": breaking})
    elif cmd == "new-context":
        values = {
            "paths": opt(a, "--paths", ".corpus/…"),
            "source": opt(a, "--source", "manual"),
        }
        create("context", a[1], a[2], a[3], values)
    elif cmd == "new-github":
        values = {
            "paths": opt(a, "--paths", ".github/…"),
            "source": opt(a, "--source", "manual"),
            "validated_by": opt(a, "--validated-by", PENDING).replace('"', "'"),
        }
        create("github", a[1], a[2], a[3], values)
    elif cmd == "list":
        kinds = [opt(a, "--kind")] if opt(a, "--kind") else list(DIRS)
        for kind in kinds:
            for p in fragments(kind, opt(a, "--issue")):
                meta, body = split(p.read_text(encoding="utf-8"))
                first = next((ln for ln in body.splitlines() if ln.strip()), "")
                print(
                    f"{p.relative_to(ROOT)}  [{kind}, {(meta or {}).get('agent')}]  "
                    f"{first[:90]}"
                )
    elif cmd == "show":
        n = opt(a, "--issue")
        for kind in DIRS:
            for p in fragments(kind, n):
                print(f"===== {p.relative_to(ROOT)}\n{p.read_text(encoding='utf-8')}")
    elif cmd == "issues":
        found = [
            n for n in [branch_issue(git("rev-parse", "--abbrev-ref", "HEAD"))] if n
        ]
        base = default_base()
        log = git("log", "--format=%B", f"{base}..HEAD") if base else ""
        for n in re.findall(r"#(\d+)", log):
            if n not in found:
                found.append(n)
        print(" ".join(found))
    elif cmd == "check":
        problems = check(
            ROOT,
            opt(a, "--base"),
            opt(a, "--head"),
            opt(a, "--branch"),
            "--no-worktree" not in a,
        )
        for p in problems:
            print("FAIL", p)
        print("OK" if not problems else f"{len(problems)} problem(s)")
        sys.exit(1 if problems else 0)
    elif cmd == "brief":
        print(brief())
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

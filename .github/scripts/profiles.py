#!/usr/bin/env python3
"""Read and write the PROFILE blocks of the agent files and copilot-instructions.md.

A PROFILE block sits between <!-- PROFILE:START --> and <!-- PROFILE:END -->.
cloud-init writes it directly, after the user approves the content. Every write is
a .github change, logged in .changes/github/ with the user's approval.

Keys and files (template)
  architect, data, devops, security, project-master
      -> .github/agents/<agent>.agent.md (profile.md)
  instructions
      -> .github/copilot-instructions.md (instructions-profile.md)

Commands
  profiles.py list                    every profile, its file, status and size
  profiles.py get <key>               print a profile body
  profiles.py set <key> <body-file>   replace a profile body, nothing else
  profiles.py check                   one block per file, template keys, sizes
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
AGENTS = {
    "architect": "cloud-architect",
    "data": "cloud-data-engineer",
    "devops": "cloud-devops-engineer",
    "security": "cloud-security-engineer",
    "project-master": "project-master",
}
BLOCK_RE = re.compile(r"(<!-- PROFILE:START -->\n)(.*?)(<!-- PROFILE:END -->)", re.S)
LIMITS = {"agent": 6000, "instructions": 9000}
AGENT_PROMPT_MAX = 30000


def target(key):
    if key == "instructions":
        return (
            ROOT / ".github" / "copilot-instructions.md",
            "instructions-profile.md",
            "instructions",
        )
    if key in AGENTS:
        return (
            ROOT / ".github" / "agents" / f"{AGENTS[key]}.agent.md",
            "profile.md",
            "agent",
        )
    sys.exit(f"unknown key '{key}'. Use one of: {', '.join([*AGENTS, 'instructions'])}")


def keys():
    return [*AGENTS, "instructions"]


def block(key):
    path, _, _ = target(key)
    text = path.read_text(encoding="utf-8")
    matches = list(BLOCK_RE.finditer(text))
    return path, text, matches


def status(body):
    s = re.search(r"INIT-STATUS:\s*(\w+)", body or "")
    d = re.search(r"INIT-DATE:\s*(\S+)", body or "")
    return f"{s.group(1) if s else 'unknown'}{' ' + d.group(1) if d else ''}"


def required(template_name):
    """A profile's required lines: its KEY: lines and its ### headings."""
    text = (ROOT / ".github" / "templates" / template_name).read_text(encoding="utf-8")
    found = [
        m.group(1) + ":"
        for m in re.finditer(r"^([A-Z][A-Z -]*?(?:\([^)]*\))?):", text, re.M)
    ]
    return found + [ln.strip() for ln in text.splitlines() if ln.startswith("#")]


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd = a[0]
    if cmd == "list":
        for key in keys():
            path, _, m = block(key)
            body = m[0].group(2) if len(m) == 1 else ""
            rel = path.relative_to(ROOT)
            print(f"{key:15} {rel}  [{status(body)}]  {len(body)} chars")
    elif cmd == "get":
        path, _, m = block(a[1])
        if len(m) != 1:
            sys.exit(
                f"{path.relative_to(ROOT)}: expected one PROFILE block, found {len(m)}"
            )
        sys.stdout.write(m[0].group(2))
    elif cmd == "set":
        key, body_file = a[1], a[2]
        path, tpl, kind = target(key)
        body = pathlib.Path(body_file).read_text(encoding="utf-8").strip("\n") + "\n"
        if "PROFILE:" in body:
            sys.exit("body must not contain PROFILE markers")
        if len(body) > LIMITS[kind]:
            sys.exit(f"refusing: profile is {len(body)} chars (limit {LIMITS[kind]})")
        _, text, m = block(key)
        if len(m) != 1:
            sys.exit(
                f"{path.relative_to(ROOT)}: expected one PROFILE block, found {len(m)}"
            )
        old = m[0].group(2)
        if "OWNER NOTES:" in old and "OWNER NOTES:" not in body:
            sys.exit(
                "refusing: keep the existing OWNER NOTES verbatim in the new profile"
            )
        new = text[: m[0].start(2)] + body + text[m[0].end(2) :]
        if kind == "agent" and len(new.split("\n---\n", 1)[-1]) > AGENT_PROMPT_MAX:
            sys.exit(f"refusing: agent prompt would exceed {AGENT_PROMPT_MAX} chars")
        path.write_text(new, encoding="utf-8")
        print(f"updated the PROFILE block of {path.relative_to(ROOT)}")
    elif cmd == "check":
        ok = True
        for key in keys():
            path, tpl, kind = target(key)
            _, text, m = block(key)
            problems = []
            if len(m) != 1:
                problems.append(f"{len(m)} PROFILE blocks (expected 1)")
            else:
                body = m[0].group(2)
                if not status(body).startswith("pending"):
                    problems += [f"missing {r}" for r in required(tpl) if r not in body]
                if len(body) > LIMITS[kind]:
                    problems.append(f"{len(body)} chars > {LIMITS[kind]}")
            if kind == "agent" and not text.startswith("---\n"):
                problems.append("front matter missing")
            ok &= not problems
            body_status = status(m[0].group(2)) if len(m) == 1 else "-"
            rel = path.relative_to(ROOT)
            mark = "ok " if not problems else "BAD"
            print(f"{mark} {key:15} {rel}  [{body_status}] {'; '.join(problems)}")
        sys.exit(0 if ok else 1)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

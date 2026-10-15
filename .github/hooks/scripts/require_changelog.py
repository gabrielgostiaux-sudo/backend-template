#!/usr/bin/env python3
"""agentStop: before the agent finishes, every change is logged in .changes/.

- work -> .changes/unreleased/, corpus -> .changes/context/,
  .github -> .changes/github/ (validated-by records the user's explicit approval)
- lint, type and formatting fixes ([CLEAN] commits, whitespace-only edits)
  need no fragment

Same rules as CI (`.github/scripts/changes.py check`). It never blocks a tool
call: it asks the agent once to finish its logging. When the runtime reports that
this turn was already forced to continue (stop_hook_active), the agent may stop.
"""

import contextlib
import importlib
import json
import pathlib
import shutil
import subprocess
import sys


def repo_root(cwd):
    git = shutil.which("git")
    if not git:
        return ""
    # Arguments are passed as a list, never through a shell.
    r = subprocess.run(  # noqa: S603
        [git, "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout.strip()


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return
    if data.get("stop_hook_active") or data.get("stopHookActive"):
        return
    root = repo_root(data.get("cwd") or pathlib.Path.cwd())
    if not root:
        return
    sys.dont_write_bytecode = True  # never leave __pycache__ inside .github/
    sys.path.insert(0, str(pathlib.Path(root) / ".github" / "scripts"))
    changes = importlib.import_module("changes")

    problems = changes.check(root)
    if problems:
        reason = (
            "Log your changes before finishing: "
            + " ".join(problems[:6])
            + " Fragments follow .github/templates/"
            " (fragment.md, context-change.md, github-change.md)."
        )
        sys.stdout.write(json.dumps({"decision": "block", "reason": reason}) + "\n")


if __name__ == "__main__":
    with contextlib.suppress(Exception):
        main()
    sys.exit(0)

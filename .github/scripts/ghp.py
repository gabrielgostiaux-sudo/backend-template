#!/usr/bin/env python3
"""Thin wrapper over `gh project` for project-master's board updates (Projects v2).

The project is the one recorded at bootstrap in .github/project/check_project.json
("project": {"owner", "number", "repository"}). /project-bootstrap creates it.

Commands
  ghp.py fields                          list fields and options
  ghp.py items [--json]                  list items with their field values (read-only)
  ghp.py add <issue|pr|url> [Field=Value ...]   add an item (idempotent), set fields
  ghp.py set <issue|pr> Field=Value [...]       set fields on an existing item

Values: single-select by option name ("Status=In progress"), numbers, dates
YYYY-MM-DD, text otherwise. Iteration fields are not set here (use the UI or
GraphQL). Needs `gh auth refresh -s project`.
"""

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CFG = ROOT / ".github" / "project" / "check_project.json"


def gh(*args, parse=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed:\n{r.stderr.strip()}")
    return json.loads(r.stdout) if parse and r.stdout.strip() else r.stdout


def cfg():
    if not CFG.exists():
        sys.exit("No .github/project/check_project.json: run /project-bootstrap first.")
    p = json.loads(CFG.read_text())["project"]
    if "__FILL__" in json.dumps(p):
        sys.exit("check_project.json still has placeholders.")
    return p


def proj(p):
    return [str(p["number"]), "--owner", p["owner"]]


def fields(p):
    return gh("project", "field-list", *proj(p), "--format", "json", "--limit", "100")[
        "fields"
    ]


def project_id(p):
    return gh("project", "view", *proj(p), "--format", "json")["id"]


def items(p):
    return gh("project", "item-list", *proj(p), "--format", "json", "--limit", "1000")[
        "items"
    ]


def find_item(p, number):
    for it in items(p):
        content = it.get("content") or {}
        if (
            str(content.get("number")) == str(number)
            and p["repository"].lower() in str(content.get("url", "")).lower()
        ):
            return it
    return None


def set_fields(p, item_id, pairs):
    fl = {f["name"].lower(): f for f in fields(p)}
    pid = project_id(p)
    for pair in pairs:
        name, _, value = pair.partition("=")
        f = fl.get(name.strip().lower())
        if not f:
            sys.exit(
                f"unknown field '{name}'. "
                f"Known: {', '.join(x['name'] for x in fl.values())}"
            )
        base = [
            "project",
            "item-edit",
            "--id",
            item_id,
            "--project-id",
            pid,
            "--field-id",
            f["id"],
        ]
        if f.get("options") is not None:
            opt = next(
                (o for o in f["options"] if o["name"].lower() == value.strip().lower()),
                None,
            )
            if not opt:
                sys.exit(
                    f"field '{f['name']}' has no option '{value}'. "
                    f"Options: {', '.join(o['name'] for o in f['options'])}"
                )
            gh(*base, "--single-select-option-id", opt["id"], parse=False)
        elif f.get("type") == "ProjectV2IterationField":
            print(f"  skipped {f['name']}: set iterations in the UI or via GraphQL")
            continue
        else:
            v = value.strip()
            kind = (
                "--date"
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v)
                else "--number"
                if re.fullmatch(r"-?\d+(\.\d+)?", v)
                else "--text"
            )
            gh(*base, kind, v, parse=False)
        print(f"  {f['name']} = {value}")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    p = cfg()
    if a[0] == "fields":
        for f in fields(p):
            print(
                f"{f['name']:20} {f['type']:28} "
                f"{', '.join(o['name'] for o in f.get('options') or [])}"
            )
    elif a[0] == "items":
        its = items(p)
        if "--json" in a:
            print(json.dumps(its, indent=2))
            return
        for it in its:
            content = it.get("content") or {}
            extras = {
                k: v
                for k, v in it.items()
                if k
                not in ("id", "content", "title", "repository", "labels", "assignees")
                and isinstance(v, (str, int, float))
            }
            print(
                f"#{content.get('number', '?'):<5} "
                f"{str(it.get('title', ''))[:60]:60} {extras}"
            )
    elif a[0] == "add":
        ref = a[1]
        num = ref.rstrip("/").split("/")[-1]
        it = find_item(p, num)
        if it:
            item_id = it["id"]
            print(f"#{num} already on the board")
        else:
            url = (
                ref
                if ref.startswith("http")
                else f"https://github.com/{p['repository']}/issues/{num}"
            )
            item_id = gh(
                "project", "item-add", *proj(p), "--url", url, "--format", "json"
            )["id"]
            print(f"added #{num}")
        set_fields(p, item_id, a[2:])
    elif a[0] == "set":
        it = find_item(p, a[1])
        if not it:
            sys.exit(f"#{a[1]} is not on the board; use `add`")
        print(f"#{a[1]}:")
        set_fields(p, it["id"], a[2:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

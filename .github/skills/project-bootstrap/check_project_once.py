#!/usr/bin/env python3
"""Read-only verification of a project bootstrap described by a JSON manifest."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class CheckFailure(Exception):
    """Raised when a check cannot be completed safely."""


def run_json(*args: str) -> Any:
    result = subprocess.run(
        ["gh", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise CheckFailure(f"GitHub CLI command failed: gh {' '.join(args)}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise CheckFailure(
            f"GitHub CLI returned invalid JSON: gh {' '.join(args)}"
        ) from error


def require_filled(value: Any, location: str = "config") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require_filled(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            require_filled(child, f"{location}[{index}]")
    elif isinstance(value, str) and (
        "__FILL__" in value or value.startswith("<") and value.endswith(">")
    ):
        raise CheckFailure(f"Configuration still has a placeholder at {location}.")


def issue_url(item: dict[str, Any]) -> str | None:
    content = item.get("content")
    if isinstance(content, dict):
        url = content.get("url")
        if isinstance(url, str):
            return url

    url = item.get("url")
    return url if isinstance(url, str) else None


def get_item_status(item: dict[str, Any]) -> str | None:
    status = item.get("status")
    if isinstance(status, str):
        return status

    fields = item.get("fieldValues")
    if isinstance(fields, list):
        for field in fields:
            if field.get("name") == "Status":
                option = field.get("option")
                if isinstance(option, str):
                    return option
                if isinstance(option, dict):
                    return option.get("name")

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        type=Path,
        help="Filled project-check JSON file generated from the template",
    )
    args = parser.parse_args()

    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        require_filled(config)

        project_config = config["project"]
        owner = project_config["owner"]
        number = int(project_config["number"])
        repository = project_config["repository"]
        expected_title = project_config["title"]

        project_args = ["--owner", owner, "--format", "json"]
        project = run_json("project", "view", str(number), *project_args)
        fields_result = run_json("project", "field-list", str(number), *project_args)
        items_result = run_json(
            "project",
            "item-list",
            str(number),
            *project_args,
            "--limit",
            "1000",
        )
        issues = run_json(
            "issue",
            "list",
            "--repo",
            repository,
            "--state",
            "all",
            "--limit",
            "1000",
            "--json",
            "number,title,body,url",
        )
        labels = run_json(
            "label",
            "list",
            "--repo",
            repository,
            "--limit",
            "1000",
            "--json",
            "name",
        )
        milestones = run_json(
            "api",
            f"repos/{repository}/milestones?state=all&per_page=100",
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(
            f"ERROR: Invalid or unreadable verifier configuration: {error}",
            file=sys.stderr,
        )
        return 2
    except CheckFailure as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    errors: list[str] = []

    if project.get("number") != number:
        errors.append(f"Project number mismatch: expected {number}.")
    if project.get("title") != expected_title:
        errors.append(
            f"Project title mismatch: expected {expected_title!r}, "
            f"found {project.get('title')!r}."
        )

    fields = fields_result.get("fields", [])
    fields_by_name = {field.get("name"): field for field in fields}

    for expected in config.get("fields", []):
        name = expected["name"]
        field = fields_by_name.get(name)
        if field is None:
            errors.append(f"Missing project field: {name}")
            continue

        expected_type = expected["type"]
        actual_type = field.get("type", "")
        if expected_type == "single_select":
            if not actual_type.endswith("SingleSelectField"):
                errors.append(f"Field {name} is not a single-select field.")
            actual_options = {option.get("name") for option in field.get("options", [])}
            wanted_options = set(expected.get("options", []))
            if actual_options != wanted_options:
                errors.append(
                    f"Field {name} options differ: expected "
                    f"{sorted(wanted_options)}, found {sorted(actual_options)}."
                )
        elif expected_type == "text":
            if actual_type != "ProjectV2Field":
                errors.append(
                    f"Field {name} has unexpected type {actual_type!r}; "
                    "expected a text field."
                )
        else:
            errors.append(
                f"Unsupported configured field type for {name}: {expected_type}"
            )

    for expected in config.get("status_fields", []):
        field = fields_by_name.get(expected["name"])
        if field is None:
            errors.append(f"Missing status field: {expected['name']}")
            continue
        options = {option.get("name") for option in field.get("options", [])}
        wanted = set(expected["options"])
        if options != wanted:
            errors.append(
                f"Status options differ: expected {sorted(wanted)}, "
                f"found {sorted(options)}."
            )

    actual_milestones = {milestone.get("title") for milestone in milestones}
    for title in config.get("milestones", []):
        if title not in actual_milestones:
            errors.append(f"Missing milestone: {title}")

    actual_labels = {label.get("name") for label in labels}
    for name in config.get("labels", []):
        if name not in actual_labels:
            errors.append(f"Missing label: {name}")

    issues_by_key: dict[str, list[dict[str, Any]]] = {}
    for issue in issues:
        body = issue.get("body") or ""
        for expected in config.get("issues", []):
            marker = f"<!-- pm-key: {expected['key']} -->"
            if marker in body:
                issues_by_key.setdefault(expected["key"], []).append(issue)

    project_items = items_result.get("items", [])
    items_by_url = {
        url: item for item in project_items if (url := issue_url(item)) is not None
    }

    for expected in config.get("issues", []):
        key = expected["key"]
        matches = issues_by_key.get(key, [])
        if len(matches) != 1:
            errors.append(f"{key}: expected one matching issue, found {len(matches)}.")
            continue

        issue = matches[0]
        if issue.get("title") != expected["title"]:
            errors.append(
                f"{key}: title mismatch; expected {expected['title']!r}, "
                f"found {issue.get('title')!r}."
            )
        if issue.get("url") not in items_by_url:
            errors.append(f"{key}: issue is not in the selected project.")

    for expected in config.get("preserved_items", []):
        url = expected["url"]
        item = items_by_url.get(url)
        if item is None:
            errors.append(f"Previously existing project item is missing: {url}")
            continue

        expected_status = expected.get("status")
        if expected_status is not None:
            actual_status = get_item_status(item)
            if actual_status != expected_status:
                errors.append(
                    f"Existing item status changed for {url}: expected "
                    f"{expected_status!r}, found {actual_status!r}."
                )

    if errors:
        print(f"FAILED: {len(errors)} check(s) need attention.")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "OK: project, configured fields, milestones, labels, keyed issues, "
        f"and {len(config.get('preserved_items', []))} preserved items verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

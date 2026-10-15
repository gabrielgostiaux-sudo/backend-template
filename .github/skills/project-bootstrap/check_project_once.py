#!/usr/bin/env python3
"""Read-only verification of a project bootstrap described by a JSON manifest."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


class CheckFailureError(Exception):
    """Raised when a check cannot be completed safely."""


def out(text: str, stream: Any = sys.stdout) -> None:
    stream.write(f"{text}\n")


def run_json(*args: str) -> Any:
    gh = shutil.which("gh")
    if not gh:
        raise CheckFailureError("GitHub CLI (gh) is not installed or not on PATH")
    # Arguments are passed as a list, never through a shell.
    result = subprocess.run(  # noqa: S603
        [gh, *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise CheckFailureError(f"GitHub CLI command failed: gh {' '.join(args)}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise CheckFailureError(
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
        "__FILL__" in value or (value.startswith("<") and value.endswith(">"))
    ):
        raise CheckFailureError(f"Configuration still has a placeholder at {location}.")


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


def fetch(config: dict[str, Any]) -> dict[str, Any]:
    """Read everything the checks need from GitHub (read-only)."""
    project_config = config["project"]
    number = int(project_config["number"])
    repository = project_config["repository"]
    project_args = ["--owner", project_config["owner"], "--format", "json"]
    return {
        "number": number,
        "title": project_config["title"],
        "project": run_json("project", "view", str(number), *project_args),
        "fields": run_json("project", "field-list", str(number), *project_args),
        "items": run_json(
            "project", "item-list", str(number), *project_args, "--limit", "1000"
        ),
        "issues": run_json(
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
        ),
        "labels": run_json(
            "label", "list", "--repo", repository, "--limit", "1000", "--json", "name"
        ),
        "milestones": run_json(
            "api", f"repos/{repository}/milestones?state=all&per_page=100"
        ),
    }


def check_project(data: dict[str, Any]) -> list[str]:
    errors = []
    project = data["project"]
    if project.get("number") != data["number"]:
        errors.append(f"Project number mismatch: expected {data['number']}.")
    if project.get("title") != data["title"]:
        errors.append(
            f"Project title mismatch: expected {data['title']!r}, "
            f"found {project.get('title')!r}."
        )
    return errors


def check_field(expected: dict[str, Any], field: dict[str, Any]) -> list[str]:
    name = expected["name"]
    expected_type = expected["type"]
    actual_type = field.get("type", "")
    errors = []
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
        errors.append(f"Unsupported configured field type for {name}: {expected_type}")
    return errors


def check_fields(config: dict[str, Any], fields_by_name: dict[str, Any]) -> list[str]:
    errors = []
    for expected in config.get("fields", []):
        field = fields_by_name.get(expected["name"])
        if field is None:
            errors.append(f"Missing project field: {expected['name']}")
        else:
            errors += check_field(expected, field)

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
    return errors


def check_named(config: dict[str, Any], data: dict[str, Any]) -> list[str]:
    actual_milestones = {milestone.get("title") for milestone in data["milestones"]}
    actual_labels = {label.get("name") for label in data["labels"]}
    errors = [
        f"Missing milestone: {title}"
        for title in config.get("milestones", [])
        if title not in actual_milestones
    ]
    errors += [
        f"Missing label: {name}"
        for name in config.get("labels", [])
        if name not in actual_labels
    ]
    return errors


def check_issues(
    config: dict[str, Any], data: dict[str, Any], items_by_url: dict[str, Any]
) -> list[str]:
    issues_by_key: dict[str, list[dict[str, Any]]] = {}
    for issue in data["issues"]:
        body = issue.get("body") or ""
        for expected in config.get("issues", []):
            marker = f"<!-- pm-key: {expected['key']} -->"
            if marker in body:
                issues_by_key.setdefault(expected["key"], []).append(issue)

    errors = []
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
    return errors


def check_preserved(config: dict[str, Any], items_by_url: dict[str, Any]) -> list[str]:
    errors = []
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
    return errors


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
        data = fetch(config)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        out(f"ERROR: Invalid or unreadable verifier configuration: {error}", sys.stderr)
        return 2
    except CheckFailureError as error:
        out(f"ERROR: {error}", sys.stderr)
        return 2

    fields_by_name = {
        field.get("name"): field for field in data["fields"].get("fields", [])
    }
    items_by_url = {
        url: item
        for item in data["items"].get("items", [])
        if (url := issue_url(item)) is not None
    }
    errors = [
        *check_project(data),
        *check_fields(config, fields_by_name),
        *check_named(config, data),
        *check_issues(config, data, items_by_url),
        *check_preserved(config, items_by_url),
    ]

    if errors:
        out(f"FAILED: {len(errors)} check(s) need attention.")
        for error in errors:
            out(f"- {error}")
        return 1

    out(
        "OK: project, configured fields, milestones, labels, keyed issues, "
        f"and {len(config.get('preserved_items', []))} preserved items verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

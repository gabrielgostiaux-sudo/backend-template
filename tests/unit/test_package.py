"""Smoke tests for the application package."""

import my_project_template


def test_package_can_be_imported() -> None:
    assert my_project_template.__doc__ == "Application package."

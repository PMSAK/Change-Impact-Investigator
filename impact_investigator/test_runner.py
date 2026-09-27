import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Union


def run_tests(
    project_root: str,
    test_path: Union[str, List[str]] = "",
) -> Dict:
    """
    Run pytest and return structured information about the result.

    test_path can be:
        - a single pytest path/node ID
        - a list of pytest paths/node IDs

    Returns:
        {
            "passed": int,
            "failed": int,
            "errors": int,
            "total": int,
            "passed_tests": [pytest node IDs],
            "failed_tests": [pytest node IDs],
            "returncode": int,
            "output": str,
        }
    """

    project_root_path = Path(project_root).resolve()

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
    ]

    # ---------------------------------------------------------------
    # Normalize test paths
    # ---------------------------------------------------------------

    if test_path:
        if isinstance(test_path, str):
            test_paths = [test_path]
        else:
            test_paths = test_path

        normalized_paths = []

        for path in test_paths:

            # Separate filesystem path from pytest node ID.
            if "::" in path:
                file_path, node = path.split("::", 1)
            else:
                file_path, node = path, ""

            file_path = Path(file_path)

            # Resolve relative paths against the repository first.
            if file_path.is_absolute():
                candidate = file_path.resolve()
            else:
                candidate = (project_root_path / file_path).resolve()

                if not candidate.exists():
                    candidate = (Path.cwd() / file_path).resolve()

            # Prevent paths outside the repository from being executed.
            try:
                file_path = candidate.relative_to(project_root_path)
            except ValueError:
                raise ValueError(
                    "Test path must be located inside the repository."
                )

            normalized = file_path.as_posix()

            if node:
                normalized += "::" + node

            normalized_paths.append(normalized)

        command.extend(normalized_paths)

    # ---------------------------------------------------------------
    # Run pytest
    # ---------------------------------------------------------------

    result = subprocess.run(
        command,
        cwd=project_root_path,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    # ---------------------------------------------------------------
    # Extract failed tests
    # ---------------------------------------------------------------

    failed_tests = []

    for line in output.splitlines():

        if line.startswith("FAILED "):

            nodeid = line[len("FAILED "):].strip()

            # Remove trailing assertion message.
            if " - " in nodeid:
                nodeid = nodeid.split(" - ", 1)[0]

            failed_tests.append(nodeid)

    # ---------------------------------------------------------------
    # Extract passed tests
    # ---------------------------------------------------------------
    #
    # IMPORTANT:
    # pytest's "-q" output gives us the counts, but it does not
    # normally print every passing node ID.
    #
    # Therefore, when specific test node IDs were requested, we can
    # determine the passing tests by taking the requested tests that
    # did not appear in failed_tests.
    #
    # This prevents the UI from blindly treating every non-failed
    # test as passed when pytest actually reported an error.
    # ---------------------------------------------------------------

    requested_tests = []

    if test_path:
        if isinstance(test_path, str):
            requested_tests = [test_path]
        else:
            requested_tests = list(test_path)

    # Normalize requested IDs in the same way as failed IDs.
    normalized_requested_tests = []

    for test_id in requested_tests:
        normalized_id = str(test_id).replace("\\", "/")
        normalized_requested_tests.append(normalized_id)

    normalized_failed_tests = {
        str(test_id).replace("\\", "/")
        for test_id in failed_tests
    }

    passed_tests = [
        test_id
        for test_id in normalized_requested_tests
        if test_id not in normalized_failed_tests
    ]

    # ---------------------------------------------------------------
    # Extract summary counts
    # ---------------------------------------------------------------

    passed_match = re.search(
        r"(\d+)\s+passed",
        output,
    )

    failed_match = re.search(
        r"(\d+)\s+failed",
        output,
    )

    errors_match = re.search(
        r"(\d+)\s+errors?",
        output,
    )

    passed = (
        int(passed_match.group(1))
        if passed_match
        else 0
    )

    failed = (
        int(failed_match.group(1))
        if failed_match
        else 0
    )

    errors = (
        int(errors_match.group(1))
        if errors_match
        else 0
    )

    total = passed + failed + errors

    # ---------------------------------------------------------------
    # Important correction:
    #
    # If pytest reports errors, the tests involved in those errors
    # must not be considered passed merely because they weren't listed
    # under FAILED.
    # ---------------------------------------------------------------

    if errors > 0:
        passed_tests = [
            test_id
            for test_id in passed_tests
            if test_id not in normalized_failed_tests
        ]

    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "total": total,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "returncode": result.returncode,
        "output": output,
    }
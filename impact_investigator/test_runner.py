import re
import subprocess
import sys
from typing import List, Dict, Union
from pathlib import Path


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
            "failed_tests": [pytest node IDs],
            "returncode": int,
            "output": str,
        }
    """

    command = [sys.executable, "-m", "pytest", "-q"]

    if test_path:
        if isinstance(test_path, str):
            test_paths = [test_path]
        else:
            test_paths = test_path

        # Pytest node IDs use "/" as the path separator.
        normalized_paths = []

        for path in test_paths:
            # Separate the filesystem path from the pytest node ID.
            if "::" in path:
                file_path, node = path.split("::", 1)
            else:
                file_path, node = path, ""

            file_path = Path(file_path)

            # If the path exists from the current process, convert it
            # to an absolute path before pytest changes into project_root.
            if not file_path.is_absolute():
                file_path = file_path.resolve()

            normalized = str(file_path).replace("\\", "/")

            if node:
                normalized += "::" + node

            normalized_paths.append(normalized)

        test_paths = normalized_paths

        command.extend(test_paths)

    result = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    failed_tests = []

    # Example:
    # FAILED demo_project/tests/test_pricing.py::TestSubtotal::test_single_item
    for line in output.splitlines():
        if line.startswith("FAILED "):
            nodeid = line[len("FAILED "):].strip()

            # Remove trailing " - ..." if pytest added an assertion message
            if " - " in nodeid:
                nodeid = nodeid.split(" - ", 1)[0]

            failed_tests.append(nodeid)

    passed_match = re.search(r"(\d+)\s+passed", output)
    failed_match = re.search(r"(\d+)\s+failed", output)
    errors_match = re.search(r"(\d+)\s+errors?", output)

    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errors = int(errors_match.group(1)) if errors_match else 0

    total = passed + failed + errors

    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "total": total,
        "failed_tests": failed_tests,
        "returncode": result.returncode,
        "output": output,
    }
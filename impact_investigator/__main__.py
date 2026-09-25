"""
__main__.py
~~~~~~~~~~~
CLI entry point for the Change Impact Investigator.

Usage
-----
    python -m impact_investigator <target_path> [target_func] [options]

Examples
--------
    # Analyse a specific function in a file
    python -m impact_investigator demo_project/app/pricing.py calculate_discount

    # Analyse at file level (no specific function)
    python -m impact_investigator demo_project/app/pricing.py

    # Specify a custom project root and test directory
    python -m impact_investigator demo_project/app/pricing.py calculate_discount \\
        --root demo_project \\
        --tests demo_project/tests
"""

import argparse
import io
import os
import sys

# Force UTF-8 output on Windows so non-ASCII report characters are not rejected
# by the default cp1252 console codec.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from impact_investigator.reporter import build_report, format_report


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m impact_investigator",
        description="Analyse the impact of a Python source change.",
    )
    parser.add_argument(
        "target_path",
        help="Path to the Python file that was changed.",
    )
    parser.add_argument(
        "target_func",
        nargs="?",
        default=None,
        help="Name of the specific function that was changed (optional).",
    )
    parser.add_argument(
        "--root",
        default=None,
        help=(
            "Project root directory to scan for the call graph. "
            "Defaults to the directory containing target_path."
        ),
    )
    parser.add_argument(
        "--tests",
        default=None,
        action="append",
        dest="test_dirs",
        metavar="TEST_DIR",
        help=(
            "Directory to scan for tests. Can be repeated. "
            "Defaults to the project root."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the report as JSON instead of plain text.",
    )

    args = parser.parse_args(argv)

    # Resolve target path
    target_path = os.path.abspath(args.target_path)
    if not os.path.isfile(target_path):
        print(f"Error: file not found: {args.target_path}", file=sys.stderr)
        return 1

    # Resolve project root
    root = os.path.abspath(args.root) if args.root else os.path.dirname(target_path)

    # Resolve test dirs
    test_dirs = (
        [os.path.abspath(d) for d in args.test_dirs]
        if args.test_dirs
        else None
    )

    # Build report
    report = build_report(
        target_path=target_path,
        target_func=args.target_func,
        project_root=root,
        test_dirs=test_dirs,
    )

    if args.json:
        import json

        def _serialise(obj):
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            if hasattr(obj, "__slots__"):
                return {s: getattr(obj, s) for s in obj.__slots__}
            return str(obj)

        # Build a JSON-friendly version of the report
        json_report = {
            "target_file": report["target_file"],
            "target_func": report["target_func"],
            "direct_callees": [
                {"module": c.module, "name": c.name, "file": c.file_path, "line": c.lineno}
                for c in report["direct_callees"]
            ],
            "direct_callers": [
                {"module": c.module, "name": c.name, "file": c.file_path, "line": c.lineno}
                for c in report["direct_callers"]
            ],
            "indirect_callers": {
                str(depth): [
                    {"module": c.module, "name": c.name, "file": c.file_path, "line": c.lineno}
                    for c in infos
                ]
                for depth, infos in report["indirect_callers"].items()
            },
            "related_tests": [
                {"pytest_id": t.pytest_id, "file": t.file_path}
                for t in report["related_tests"]
            ],
            "coverage_gaps": report["coverage_gaps"],
            "git_file_history": [
                {"sha": ci.short_sha, "date": ci.date, "author": ci.author, "message": ci.message}
                for ci in report["git_file_history"]
            ],
            "git_func_history": [
                {"sha": ci.short_sha, "date": ci.date, "author": ci.author, "message": ci.message}
                for ci in report["git_func_history"]
            ],
            "risk_summary": report["risk_summary"],
        }
        print(json.dumps(json_report, indent=2))
    else:
        print(format_report(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())

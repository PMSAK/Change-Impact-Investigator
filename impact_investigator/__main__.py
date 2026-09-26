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
    python -m impact_investigator demo_project/app/pricing.py calculate_discount \
        --root demo_project \
        --tests demo_project/tests

    # Analyse all functions changed in the working tree
    python -m impact_investigator --working-tree --root demo_project

    # Working-tree analysis as JSON
    python -m impact_investigator --working-tree --root demo_project --json
"""

import argparse
import io
import json
import os
import sys

from impact_investigator.engine import analyze_question

from impact_investigator.serialization import report_to_json


# Force UTF-8 output on Windows so non-ASCII report characters
# are not rejected by the default console codec.
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace",
    )


from impact_investigator.reporter import (
    build_report,
    format_report,
    analyze_working_tree,
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m impact_investigator",
        description="Analyse the impact of a Python source change.",
    )

    # ---------------------------------------------------------------
    # Positional arguments
    # ---------------------------------------------------------------

    parser.add_argument(
        "target_path",
        nargs="?",
        default=None,
        help="Path to the Python file that was changed.",
    )

    parser.add_argument(
        "target_func",
        nargs="?",
        default=None,
        help="Name of the specific function that was changed (optional).",
    )

    # ---------------------------------------------------------------
    # General options
    # ---------------------------------------------------------------

    parser.add_argument(
        "--root",
        default=None,
        help=(
            "Project root directory to scan for the call graph. "
            "Defaults to the directory containing target_path, "
            "or the current directory in working-tree mode."
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

    # ---------------------------------------------------------------
    # Working-tree mode
    # ---------------------------------------------------------------

    parser.add_argument(
        "--working-tree",
        action="store_true",
        help="Analyse functions changed in the current working tree.",
    )

    parser.add_argument(
        "--ai",
        action="store_true",
        help="Use AI to analyze a natural-language question.",
    )

    parser.add_argument(
        "--source",
        help="Repository path, ZIP archive, or GitHub repository URL.",
    )

    parser.add_argument(
        "--question",
        help="Natural-language impact-analysis question.",
    )

    args = parser.parse_args(argv)

    # ---------------------------------------------------------------
    # AI / natural-language analysis
    # ---------------------------------------------------------------

    if args.ai:
        if not args.source:
            print("Error: --source is required when using --ai.", file=sys.stderr)
            return 1

        if not args.question:
            print("Error: --question is required when using --ai.", file=sys.stderr)
            return 1

        try:
            query, report, ai_assessment, repository_handle = (
                analyze_question(
                    source=args.source,
                    question=args.question,
                )
            )

            try:
                print("\n" + "#" * 60)
                print("  CHANGE IMPACT INVESTIGATOR")
                print("#" * 60)

                print("\n[Question]")
                print(args.question)

                print("\n" + "=" * 60)
                print("  EVIDENCE REPORT")
                print("=" * 60)

                print(format_report(report))

                print("\n" + "=" * 60)
                print("  AI IMPACT ASSESSMENT")
                print("=" * 60)

                print(ai_assessment)

            finally:
                if repository_handle is not None:
                    repository_handle.cleanup()

        except Exception as exc:
            print(
                f"Error during AI analysis: {exc}",
                file=sys.stderr,
            )
            return 1

        return 0

    # ---------------------------------------------------------------
    # Resolve project root
    # ---------------------------------------------------------------

    if args.root:
        root = os.path.abspath(args.root)

    elif args.target_path:
        root = os.path.dirname(
            os.path.abspath(args.target_path)
        )

    else:
        root = os.getcwd()

    # ---------------------------------------------------------------
    # Resolve target path
    # ---------------------------------------------------------------

    target_path = None

    if args.target_path:
        target_path = os.path.abspath(args.target_path)

        if not os.path.isfile(target_path):
            print(
                f"Error: file not found: {args.target_path}",
                file=sys.stderr,
            )
            return 1

    # A target path is required for normal analysis.
    # Working-tree analysis does not require one.
    if not args.working_tree and not target_path:
        parser.error(
            "target_path is required unless --working-tree is specified."
        )

    # ---------------------------------------------------------------
    # Resolve test directories
    # ---------------------------------------------------------------

    test_dirs = (
        [os.path.abspath(d) for d in args.test_dirs]
        if args.test_dirs
        else None
    )

    # ===============================================================
    # WORKING-TREE ANALYSIS
    # ===============================================================

    if args.working_tree:

        reports = analyze_working_tree(
            repo_root=root,
            test_dirs=test_dirs,
        )

        # -----------------------------------------------------------
        # JSON output
        # -----------------------------------------------------------

        if args.json:
            json_reports = [
                report_to_json(report)
                for report in reports
            ]

            print(
                json.dumps(
                    json_reports,
                    indent=2,
                )
            )

        # -----------------------------------------------------------
        # Human-readable output
        # -----------------------------------------------------------

        else:

            if not reports:
                print(
                    "No changed functions detected in the working tree."
                )

            else:

                for i, report in enumerate(reports):

                    print(
                        f"\n{'#' * 60}"
                    )

                    print(
                        f"  IMPACT REPORT "
                        f"{i + 1}/{len(reports)}"
                    )

                    print(
                        f"{'#' * 60}\n"
                    )

                    print(
                        format_report(report)
                    )

        return 0

    # ===============================================================
    # SINGLE-TARGET ANALYSIS
    # ===============================================================

    if target_path is None:
        parser.error(
            "target_path is required unless --working-tree is specified."
        )

    report = build_report(
        target_path=target_path,
        target_func=args.target_func,
        project_root=root,
        test_dirs=test_dirs,
    )

    # ---------------------------------------------------------------
    # JSON output
    # ---------------------------------------------------------------

    if args.json:

        json_report = report_to_json(report)

        print(
            json.dumps(
                json_report,
                indent=2,
            )
        )

    # ---------------------------------------------------------------
    # Human-readable output
    # ---------------------------------------------------------------

    else:

        print(
            format_report(report)
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
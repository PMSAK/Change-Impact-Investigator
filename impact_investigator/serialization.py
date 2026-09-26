def report_to_json(report):
    """Convert an impact report into a JSON-serializable dictionary."""

    return {
        "target_file": report["target_file"],
        "target_func": report["target_func"],
        "changed_line": report.get("changed_line"),

        "direct_callees": [
            {
                "module": c.module,
                "name": c.name,
                "file": c.file_path,
                "line": c.lineno,
            }
            for c in report["direct_callees"]
        ],

        "direct_callers": [
            {
                "module": c.module,
                "name": c.name,
                "file": c.file_path,
                "line": c.lineno,
            }
            for c in report["direct_callers"]
        ],

        "indirect_callers": {
            str(depth): [
                {
                    "module": c.module,
                    "name": c.name,
                    "file": c.file_path,
                    "line": c.lineno,
                }
                for c in infos
            ]
            for depth, infos in report["indirect_callers"].items()
        },

        "related_tests": [
            {
                "pytest_id": t.pytest_id,
                "file": t.file_path,
            }
            for t in report["related_tests"]
        ],

        "test_results": report.get("test_results", {}),

        "coverage_gaps": report["coverage_gaps"],

        "git_file_history": [
            {
                "sha": ci.short_sha,
                "date": ci.date,
                "author": ci.author,
                "message": ci.message,
            }
            for ci in report["git_file_history"]
        ],

        "git_func_history": [
            {
                "sha": ci.short_sha,
                "date": ci.date,
                "author": ci.author,
                "message": ci.message,
            }
            for ci in report["git_func_history"]
        ],

        "risk_summary": report["risk_summary"],
    }
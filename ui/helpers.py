import html


def get_field(obj, field, default=None):
    """Read a field from either a dict or a dataclass/object."""
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(field, default)

    return getattr(obj, field, default)


def risk_level(report: dict) -> str:
    text = str(report.get("risk_summary", "")).upper()

    for level in ("HIGH", "MEDIUM", "LOW"):
        if f"RISK LEVEL: {level}" in text:
            return level

    return "UNKNOWN"


def count_indirect(report: dict) -> int:
    indirect = report.get("indirect_callers") or {}

    return sum(
        len(items or [])
        for items in indirect.values()
    )


def get_test_counts(report: dict):
    results = report.get("test_results") or {}

    total = int(
        get_field(
            results,
            "total",
            len(report.get("related_tests", [])),
        ) or 0
    )

    passed = int(
        get_field(results, "passed", 0) or 0
    )

    failed = int(
        get_field(results, "failed", 0) or 0
    )

    errors = int(
        get_field(results, "errors", 0) or 0
    )

    return total, passed, failed, errors


def safe(value) -> str:
    return html.escape(str(value or ""))


def risk_class(level: str) -> str:
    return (
        level.lower()
        if level in {"LOW", "MEDIUM", "HIGH"}
        else ""
    )
# Change Impact Investigator

An evidence-backed tool that helps developers understand the potential impact of a code change.

## Problem

When a developer changes a function or module, it can be difficult to determine what else may be affected. The Change Impact Investigator combines **static call-graph analysis**, **test coverage mapping**, and **Git history** to produce an evidence-based impact report — without executing any code or calling an LLM.

---

## Architecture

```
impact_investigator/
    ast_analysis.py   — Python AST: parse files, build call graph, find callers/callees
    test_finder.py    — Scan test directories, map tests to functions, detect coverage gaps
    git_analysis.py   — Git log/diff: commits touching a file or function
    reporter.py       — Assemble evidence into a structured report dict + formatted text
    __main__.py       — CLI entry point

tests/                — Analyzer unit + integration tests (uses demo_project as fixture)

demo_project/         — Ground-truth e-commerce app for hackathon demos
    app/
        pricing.py    — calculate_subtotal, calculate_discount, calculate_tax, calculate_total
        shipping.py   — calculate_shipping, calculate_shipping_with_discount
        checkout.py   — create_order  (calls pricing + shipping)
        invoice.py    — generate_invoice  (consumes checkout order)
    tests/            — 31 pytest tests for the demo app
```

### Analysis pipeline

```
target file + function
        |
        v
  AST call graph  ──────────>  direct callers
  (whole project)              indirect callers (BFS up to depth 3)
                               direct callees
        |
        v
  Test finder  ─────────────>  related tests
  (test dirs)                  coverage gaps (structural + value-path)
        |
        v
  Git history  ─────────────>  commits touching the file
  (git log/diff)               commits touching the function (diff grep)
        |
        v
  Risk summary  ─────────────> LOW / MEDIUM / HIGH
```

---

## Setup

```bash
pip install pytest          # only dependency (for running tests)
```

No other third-party packages are required. The analyzer uses only Python's standard library (`ast`, `subprocess`, `pathlib`).

---

## Usage

```
python -m impact_investigator <target_path> [target_func] [options]
```

| Argument | Description |
|---|---|
| `target_path` | Path to the Python file that was changed |
| `target_func` | *(optional)* Name of the specific function that was changed |
| `--root DIR` | Project root to scan for the call graph (default: directory of target file) |
| `--tests DIR` | Test directory to scan (repeatable; default: project root) |
| `--json` | Emit report as JSON instead of plain text |

### Example — analyse `calculate_discount` in the demo project

```bash
python -m impact_investigator demo_project/app/pricing.py calculate_discount \
    --root demo_project \
    --tests demo_project/tests
```

Expected output (abbreviated):

```
============================================================
  CHANGE IMPACT REPORT
============================================================
Target file : demo_project/app/pricing.py
Target func : calculate_discount

[Functions called BY target] (0)
  (none detected)

[Direct callers of target] (1)
  <- app.pricing.calculate_total  (line 46  ...)

[Indirect callers] (2 across 2 depth level(s))
  depth 1  <- app.pricing.calculate_total  (line 46)
  depth 2  <- app.checkout.create_order  (line 9)

[Related tests] (13)
  [PASS] demo_project/tests/test_pricing.py::TestDiscount::test_regular_customer_gets_no_discount
  [PASS] demo_project/tests/test_pricing.py::TestDiscount::test_member_gets_five_percent
  ...

[Coverage gaps] (1)
  [WARN] Value path 'vip' in 'calculate_discount' has no test coverage
         (defined in pricing.py but never passed in a test call).

[Git history — function 'calculate_discount'] (1 commits)
  2951c3c0  2026-09-25  ...  feat: add customer discount support

------------------------------------------------------------
[Risk summary]
Function 'calculate_discount' was targeted.
  - 1 direct caller(s): app.pricing.calculate_total.
  - 2 indirect caller(s) reachable within 3 hops.
  - 13 test(s) cover this function.
  - [WARN] 1 coverage gap(s) detected (see Coverage Gaps section).
  - This function was touched in 1 commit(s) -- review Git history for context.

  Risk level: LOW
============================================================
```

### More examples

```bash
# File-level analysis (no specific function)
python -m impact_investigator demo_project/app/pricing.py \
    --root demo_project --tests demo_project/tests

# Analyse create_order in checkout
python -m impact_investigator demo_project/app/checkout.py create_order \
    --root demo_project --tests demo_project/tests

# JSON output (for tooling integration)
python -m impact_investigator demo_project/app/pricing.py calculate_discount \
    --root demo_project --tests demo_project/tests --json
```

---

## Running tests

```bash
# All tests (demo app + analyzer)
python -m pytest tests/ demo_project/tests/ -v

# Just the analyzer tests
python -m pytest tests/ -v

# Just the demo app tests
cd demo_project && python -m pytest tests/ -v
```

Expected: **103 passed** (72 analyzer + 31 demo app).

---

## What the analyzer detects

| Evidence type | What is found |
|---|---|
| **Direct callers** | Functions that call the changed function (AST call graph) |
| **Indirect callers** | BFS traversal up the call graph (up to 3 hops) |
| **Direct callees** | Functions the target itself calls |
| **Related tests** | Tests that import or call the changed function |
| **Coverage gaps — structural** | Callers or functions with zero test coverage |
| **Coverage gaps — value path** | String constants in UPPER_CASE dispatch dicts that are never passed in a test call (e.g. the intentional `"vip"` gap) |
| **Git file history** | All commits that touched the target file |
| **Git function history** | Commits whose diff mentions the function name |
| **Risk level** | Heuristic: LOW / MEDIUM / HIGH based on callers, gaps, and test count |

---

## Demo project ground truth

`demo_project/` is a small Python e-commerce order-processing application created specifically as a test fixture for this tool. It contains:

- A realistic **dependency chain**: `calculate_discount` → `calculate_total` → `create_order` → `generate_invoice`
- An **intentional coverage gap**: the `"vip"` customer type in `DISCOUNT_RATES` is never tested
- A **Git history with a bug/fix sequence**: the invoice total bug introduced after the discount feature was added (commit `feat: add customer discount support`) and fixed in `fix: correct invoice totals after discount changes`

See [`demo_project/README.md`](demo_project/README.md) for details.

---

## Hackathon

Built for the IBM Bob 2.0 Hackathon.

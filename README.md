#  Change Impact Investigator

**Understand what a code change could affect before you make it.**

Change Impact Investigator is an AI-powered developer tool that analyzes Python repositories to help developers understand the potential consequences of modifying a function.

Instead of manually tracing dependencies, searching for tests, and digging through Git history, it brings this evidence together into a structured impact report, with an AI-generated assessment to help developers decide what to investigate before merging a change.

> **Evidence first. AI second.**

##  The Problem

A small change in one function can have consequences across an entire codebase.

- Which functions depend on it?
- What other parts of the application could be affected?
- Are there relevant tests, and are they passing?
- Are there gaps in test coverage?
- What does the Git history tell us about this code?

Answering these questions manually can be time-consuming, especially in unfamiliar repositories.

**Change Impact Investigator brings these investigations into one workflow.**

##  Features

- **Dependency Analysis:** Uses Python AST-based static analysis to build a function-level call graph.
- **Direct & Indirect Impact:** Identifies callers, callees, and functions reachable through dependency relationships.
- **Test Discovery:** Finds tests related to the target function or code.
- **Test Execution:** Runs pytest and summarizes passed tests, failures, and errors.
- **Coverage Analysis:** Identifies potential coverage gaps and value-path gaps.
- **Git History Analysis:** Examines commit history and function-level changes for additional context.
- **AI-Powered Assessment:** Synthesizes the collected evidence into a readable impact assessment.
- **Interactive Dashboard:** Presents the findings through a Streamlit interface.

##  How It Works

The project follows an evidence-first analysis pipeline.

**1. Describe the change**

Provide a GitHub repository URL and describe the function or code you want to investigate.

**2. Analyze the codebase**

Python's Abstract Syntax Tree (AST) is used to parse source files, extract function definitions and calls, and construct a dependency graph.

**3. Trace potential impact**

The analyzer identifies direct callers, callees, and indirect callers to reveal relevant dependency relationships.

**4. Inspect test evidence**

The system discovers related tests, executes pytest, and examines coverage information to identify areas that may need additional testing.

**5. Examine Git history**

Git commits and function-level history provide context about previous changes to the relevant code.

**6. Generate the impact assessment**

The collected evidence is assembled into a structured report and passed to the AI reasoning layer, which explains the findings and highlights areas worth investigating.

```text
Repository + Change Question
             |
             v
      Query Parsing
             |
             v
     Python AST Analysis
             |
             v
    Dependency Call Graph
             |
             v
   Tests & Coverage Analysis
             |
             v
      Git History Analysis
             |
             v
      Structured Report
             |
             v
       AI Assessment
             |
             v
      Impact Investigation
```

##  Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application and analysis logic |
| Python AST | Static source-code and dependency analysis |
| pytest | Test discovery and execution |
| coverage.py | Test coverage analysis |
| Git | Commit history and change inspection |
| Streamlit | Interactive user interface |
| OpenAI API | AI-generated impact assessment |


##  Project Structure

```text
Change-Impact-Investigator/
│
├── impact_investigator/
│   ├── analyzer.py          # High-level repository analysis
│   ├── ast_analysis.py      # AST parsing and call graph
│   ├── engine.py            # Analysis pipeline orchestration
│   ├── query.py             # Natural-language query parsing
│   ├── reporter.py          # Structured impact report
│   ├── repository.py        # Repository preparation
│   ├── test_finder.py       # Related tests and coverage gaps
│   ├── test_runner.py       # pytest execution and results
│   ├── git_analysis.py      # Git history and change analysis
│   ├── ai_assessment.py     # AI-generated assessment
│   └── serialization.py     # Report serialization
│
├── ui/
│   ├── landing.py           # Analysis input interface
│   ├── report.py            # Results interface
│   ├── components.py        # Reusable UI components
│   ├── styles.py            # Custom styling
│   └── helpers.py           # UI helper functions
│
├── demo_project/            # Example Python repository
├── tests/                   # Automated tests
├── streamlit_app.py         # Streamlit entry point
├── requirements.txt
├── .env                     # Local secrets; do not commit
└── README.md
```

##  Design Philosophy

The central idea behind this project is to combine deterministic software analysis with AI reasoning.

The dependency graph, test results, coverage findings, and Git history provide the underlying evidence. The AI layer interprets that evidence to help developers understand the implications of a potential change.

This separation matters: an AI-generated explanation is more useful when it can be grounded in observable repository information rather than relying on guesses about the codebase.

##  Limitations

- **Static analysis is not omniscient.** Dynamic dispatch, reflection, runtime-generated behavior, and external dependencies can make some relationships difficult to identify.
- **Coverage is not correctness.** Executing a test does not guarantee that it adequately validates the behavior.
- **Impact findings are estimates.** The report identifies potential effects and areas to investigate; it cannot guarantee that every affected component has been found.
- **Repository support is focused on Python.** The AST-based dependency analysis is designed for Python source code.
- **Repository execution requires care.** Test execution should only be performed on repositories you trust.

The tool is intended to **support code review and engineering judgment, not replace them**.

##  Future Possibilities

Potential directions for further development include:

- Deeper integration with GitHub pull requests and proposed diffs.
- Improved resolution of complex cross-module and dynamic dependencies.
- More precise mapping between changed code, tests, and coverage.
- CI/CD integration to surface impact reports during code review.
- Additional language support.

##  Built During a Hackathon

Change Impact Investigator was developed for the **IBM Bob 2.0 Hackathon** as an exploration of how AI can make software engineering workflows more transparent and evidence-driven.

The project combines static code analysis, testing, coverage information, Git history, and AI reasoning to help developers investigate the potential consequences of code changes.

---

**If you find this project interesting, consider giving the repository a ⭐!**

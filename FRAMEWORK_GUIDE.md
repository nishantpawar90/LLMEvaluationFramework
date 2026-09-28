# Simple Python Evaluation Framework

This framework runs the existing test cases in `product_agent/evaluation/myEvaluations`.
The case files are left where they are and do not need to be rewritten.

## The Java/TestNG comparison

| Java automation idea | This project |
| --- | --- |
| TestNG runner | `pytest` |
| A TestNG test class or `@Test` | One existing Python file in `myEvaluations` |
| Test suite selection | `runner.py --run` or `runner.py --all` |
| Shared application behavior | `ProductAgent` and its product tools |

The `ProductAgent` is already the shared application abstraction. These cases do
not drive browser pages, so a browser-style Page Object Model would add complexity
without helping. Instead, each original case is run in its own process. This keeps
its current behavior while preventing top-level code in a case from running just
because pytest imports files during collection.

## Files to know

- `product_agent/evaluation/myEvaluations/` contains the original evaluation cases.
- `product_agent/evaluation/runner.py` discovers and launches those cases.
- `tests/test_evaluation_framework.py` connects the cases to pytest and checks the
  runner itself.
- `pytest.ini` limits default discovery to the framework's `tests` directory, so
  existing integration tests do not unexpectedly call external services.
- `pytest-html` creates a self-contained `pytest-report.html` report after each
  pytest run. The generated report is ignored by Git.
- `allure-pytest` writes Allure test results to `allure-results/`. The generated
  results and rendered report are ignored by Git.

## First steps

Open a terminal in the project directory and activate the project's virtual
environment if it is not already active. Install dependencies when needed:

```powershell
\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

List the available evaluation cases:

```powershell
python -m product_agent.evaluation.runner --list
```

Run one case by its filename:

```powershell
python -m product_agent.evaluation.runner --run TaskCompletionMetricOffline.py
```

Run every case, one after another:

```powershell
python -m product_agent.evaluation.runner --all
```

Check the framework and list the pytest evaluation tests without running them:

```powershell
pytest
```

Open `pytest-report.html` in a browser to view the test results. The report
includes passed framework checks and the skipped external-service cases.

Allure is the richer report option. After installing the Allure command-line
tool and ensuring Java is available, run pytest and then serve the report:

```powershell
pytest
allure serve allure-results
```

To create a browsable report directory instead of starting a temporary server:

```powershell
allure generate allure-results --clean -o allure-report
```

Then open `allure-report/index.html`. The pytest plugin creates result data; the
Allure command-line tool renders that data into the HTML report. Allure shows
pytest's pass/fail status; it does not by itself assert that a DeepEval metric
met its threshold.

To run the evaluation cases through pytest, explicitly opt in:

```powershell
$env:RUN_EVALUATIONS = "1"
pytest
$env:RUN_EVALUATIONS = "0"
```

## Before running evaluations

Many cases use an LLM judge, and some call `ProductAgent` and MongoDB. They may
need a valid `OPENAI_API_KEY`, the configured model, and a reachable MongoDB
instance. A case failing because a service or credential is unavailable does not
necessarily mean the runner is broken. Start with one case using `--run` before
running the full collection. The word "Offline" in a case filename does not
guarantee that it avoids all external services.
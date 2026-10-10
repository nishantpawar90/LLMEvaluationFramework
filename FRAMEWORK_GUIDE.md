# Pytest-Native Product Agent Evaluation Framework

## Purpose

This is an integration/evaluation suite for a live product-information agent. Tests call OpenAI through LangGraph, retrieve product facts from MongoDB, and use DeepEval to score results.

```text
pytest -> fixtures -> parametrized Golden -> ProductAgent -> DeepEval assertion
```

There is no custom script runner in the supported path.

## Project layout

```text
DeepEvalImp/
├── product_agent/
│   ├── agent.py                 # LangGraph agent and AgentResult
│   ├── config.py                # environment-based settings
│   ├── mongo_client.py          # safe MongoDB repository boundary
│   ├── tools.py                 # controlled LLM-callable tools
│   └── evaluation/
│       ├── dataset.py           # 15 live-data Goldens
│       ├── metrics.py           # DeepEval metrics and thresholds
│       ├── cases.py             # Golden + AgentResult -> LLMTestCase
│       └── myEvaluations/       # legacy examples, not pytest tests
├── tests/
│   ├── conftest.py              # shared fixtures
│   └── test_product_agent_evaluation.py
├── pytest.ini                   # discovery, marker, report defaults
├── requirements.txt
├── .env.example
├── CODE_WALKTHROUGH.md
└── README.md
```

## TestNG-to-pytest mapping

| TestNG concept | This framework's pytest equivalent |
| --- | --- |
| `@Test` | `test_product_agent_meets_quality_thresholds` |
| `@DataProvider` | `@pytest.mark.parametrize` with `GOLDEN_NAMES` |
| `@BeforeSuite` / `@AfterSuite` | Session-scoped fixture when needed |
| `@BeforeClass` / `@AfterClass` | Module-scoped `agent` fixture with `yield` teardown |
| TestNG groups | `@pytest.mark.evaluation` |
| `testng.xml` | `pytest.ini` plus pytest command-line selection |
| `Assert` | `deepeval.assert_test(...)`, which raises on a metric failure |
| Extent Reports | `pytest-html`; Allure is also configured |

## Safe execution

Live evaluation requires MongoDB and an OpenAI key, so tests are skipped by default:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Opt in for the current PowerShell session:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest -m evaluation -q
```

Pytest executes 15 independent test cases, one per Golden. To run only one case while debugging:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest `
  "tests/test_product_agent_evaluation.py::test_product_agent_meets_quality_thresholds[size]" -q
```

## Reports

`pytest.ini` creates `pytest-report.html` and `allure-results/`. If the Allure command-line tool is installed, render the latter with:

```powershell
allure serve allure-results
```

Generated reports and local runtime files are excluded from Git.

## Adding a scenario

1. Add a Golden in `product_agent/evaluation/dataset.py`.
2. Add the Golden name to `GOLDEN_NAMES` in `tests/test_product_agent_evaluation.py`.
3. Add or adjust a metric in `metrics.py` if needed.
4. Run the single test node first, then the marker suite.

Do not create a standalone script or subprocess runner for normal product coverage. Keep scenarios in the dataset so pytest discovers and reports them consistently.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| All 15 tests are skipped | Set `$env:RUN_EVALUATIONS = "1"`. |
| `OPENAI_API_KEY is required` | Put the key in `.env` or the process environment. |
| MongoDB connection error | Start MongoDB and load the sample UPC record. |
| One named case fails | Run that node ID alone and inspect the DeepEval reason. |
| Collection fails | Use `.\.venv\Scripts\python.exe -m pytest --collect-only -q`. |

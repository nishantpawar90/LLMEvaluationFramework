# Product agent evaluation framework

Pytest collects tests from `tests/`. A test file starts with `test_`. A test function starts with `test_`.

```text
tests/test_product_agent.py
  test_basic_lookup
  test_size
  test_category
  ...
        |
        v
ProductAgent asks MongoDB
        |
        v
deepeval.assert_test scores the answer
        |
        v
pytest pass or fail
```

The metric examples follow the same rule. `tests/test_answer_relevancy_offline.py` contains `test_answer_relevancy_offline`. There is no runner that searches for old script names and executes them.

## Layout

```text
DeepEvalImp/
├── product_agent/
│   ├── agent.py
│   ├── config.py
│   ├── mongo_client.py
│   ├── tools.py
│   └── evaluation/
│       ├── dataset.py    # questions and expected answers
│       ├── metrics.py    # DeepEval score limits
│       └── cases.py      # joins the expected answer with the agent result
├── tests/
│   ├── conftest.py       # shared setup; not a test file
│   ├── test_product_agent.py
│   └── test_*.py         # one metric example per file
└── pytest.ini
```

## TestNG comparison

| TestNG | This project |
| --- | --- |
| A test method | `def test_size(...)` |
| A test class file | `tests/test_product_agent.py` |
| `@BeforeClass` / `@AfterClass` | The `agent` fixture in `tests/conftest.py` opens the agent and closes it afterward |
| `Assert` | `deepeval.assert_test(...)` |
| `testng.xml` | `pytest.ini` |

## Run

Skipped by default:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Live run:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest -q
```

One product question:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_product_agent.py::test_size -q
```

## Add a product question

1. Add the question in `product_agent/evaluation/dataset.py`.
2. Add a new function in `tests/test_product_agent.py`, for example `def test_brand(...)`.
3. Call `_check_product_answer(..., "brand")` from that function.

## Reports

`pytest.ini` writes `pytest-report.html` and `allure-results/`.

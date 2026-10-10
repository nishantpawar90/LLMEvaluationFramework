# How these tests work

Pytest finds a test only when both names follow the same rule.

1. The file name starts with `test_`.
2. The function name starts with `test_`.

Example:

```text
tests/test_answer_relevancy_offline.py
    def test_answer_relevancy_offline():
```

Pytest does not run a Python file just because it sits in the project. A file such as `AnswerRelevancyMetricOffline.py` is invisible to pytest, because the name does not start with `test_`.

## Where to look

| File | What it is |
| --- | --- |
| `tests/test_product_agent.py` | One `test_` function for each product question, such as `test_size` and `test_reviews`. |
| `tests/test_answer_relevancy_offline.py` and the other `tests/test_*.py` files | One metric example each. Each file has one `test_` function. |
| `tests/conftest.py` | Shared setup. Pytest reads this file automatically. It is not a test, because the name does not start with `test_`. |
| `product_agent/evaluation/dataset.py` | The question and the expected answer for each product test. |
| `product_agent/evaluation/metrics.py` | The DeepEval scores used by the product tests. |

`_check_product_answer` in `tests/test_product_agent.py` is a helper. Pytest ignores it because the name starts with `_`, not `test_`. Each product question still has its own `test_` function.

## What a product test does

`test_size` asks the agent for the product size, then DeepEval scores the answer. `assert_test(...)` makes that pytest test fail when a score is below its limit.

The tests call MongoDB and OpenAI, so they stay skipped until you opt in:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest -q
```

See the names pytest found, without calling MongoDB or OpenAI:

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q
```

Run one test:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_product_agent.py::test_size -q
```

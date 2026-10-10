# Pytest-native evaluation framework

The product-agent evaluation suite uses ordinary pytest discovery rather than
launching standalone scripts through subprocesses.

```text
pytest
  -> tests/test_product_agent_evaluation.py
  -> shared fixtures in tests/conftest.py
  -> one parametrized test per Golden
  -> ProductAgent.run()
  -> DeepEval assert_test()
```

## Files and responsibilities

| File | Responsibility |
| --- | --- |
| `tests/conftest.py` | Creates shared settings, the dataset, and one reusable agent fixture. The agent is always closed during teardown. |
| `tests/test_product_agent_evaluation.py` | Declares the 15 Golden names and runs one pytest case per name. |
| `product_agent/evaluation/dataset.py` | Builds Goldens from the live MongoDB product record. |
| `product_agent/evaluation/cases.py` | Combines an expected Golden and an actual agent result into an `LLMTestCase`. |
| `product_agent/evaluation/metrics.py` | Creates fresh DeepEval metric instances and thresholds for each case. |
| `pytest.ini` | Registers the `evaluation` marker and report defaults. |

## Why this is simpler

- Every Golden is a normal pytest node, such as `...[size]`.
- A failed DeepEval threshold fails the exact pytest case through
  `deepeval.assert_test`.
- The suite does not need a custom subprocess runner.
- A module-scoped fixture starts one agent for the suite and closes it once.
- The default `pytest` command is safe: external tests remain skipped until
  `RUN_EVALUATIONS=1` is supplied.

## Run commands

Check collection without live services:

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q
```

Run the default safe command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run the live suite after starting MongoDB and setting `OPENAI_API_KEY`:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest -m evaluation -q
```

The live command calls MongoDB, OpenAI, and LLM-judged DeepEval metrics. It can
consume API usage and take several minutes.

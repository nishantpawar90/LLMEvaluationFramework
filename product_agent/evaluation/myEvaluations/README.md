# Legacy metric experiments

These standalone scripts are retained as DeepEval API examples. They are not
part of the product-agent pytest suite and are not discovered or executed by
`python -m pytest`.

The supported evaluation path is:

```powershell
$env:RUN_EVALUATIONS = "1"
python -m pytest -m evaluation -q
```

The pytest suite uses shared fixtures, parametrized Goldens, and
`deepeval.assert_test` so that each Golden is reported as an independent test.
If a legacy experiment becomes required product coverage, move its business
scenario into `dataset.py`, add an appropriate metric in `metrics.py`, and let
`tests/test_product_agent_evaluation.py` execute it.

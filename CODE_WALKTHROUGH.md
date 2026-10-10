# Product Agent: Pytest-Native Code Walkthrough

This project is an AI quality-engineering proof of concept. A LangGraph agent answers product questions through a narrow MongoDB tool boundary; pytest and DeepEval validate output and tool-selection behaviour.

## End-to-end flow

```text
tests/test_product_agent.py
  test_size()
    -> shared ProductAgent fixture
    -> LangGraph: agent -> controlled tool -> agent
    -> MongoDB product lookup
    -> AgentResult
    -> DeepEval LLMTestCase
    -> deepeval.assert_test
    -> pytest pass or failure
```

Pytest runs a function only when the file name and the function name both start with `test_`.

## Application code

### `product_agent/config.py`

`Settings` is an immutable dataclass created from environment variables. `python-dotenv` loads local `.env` values for development. Production/CI should provide the same values as environment variables.

Required runtime values are `OPENAI_API_KEY`, `MONGODB_URI`, `MONGODB_DATABASE`, and `MONGODB_COLLECTION`. `.env` is local-only; `.env.example` is the safe committed template.

### `product_agent/mongo_client.py`

`MongoProductRepository` is the only database-access boundary. It exposes a fixed `find_by_upc()` lookup rather than arbitrary MongoDB queries. It validates UPC values, returns the product document, raises `ProductNotFoundError` for an absent product, and converts PyMongo errors to `ConnectionError`.

### `product_agent/tools.py`

`product_facts()` normalizes a MongoDB document into business-friendly fields. `make_product_tools()` exposes five read-only LangChain tools:

- `get_product_by_upc`
- `get_product_review_eligibility`
- `get_product_classification`
- `get_product_dimensions`
- `get_product_sourcing`

The model receives only these tools—not a MongoDB client or arbitrary-query capability.

### `product_agent/agent.py`

`ProductAgent` builds the following LangGraph flow:

```text
START -> agent -> tools (when requested) -> agent -> END
```

`run(question)` returns an `AgentResult` containing the answer, captured tool calls, and tool outputs. The evaluation suite uses those values to verify grounding and tool behaviour.

## Evaluation code

### `product_agent/evaluation/dataset.py`

`build_dataset()` reads the configured product record and creates 13 DeepEval Goldens. Expected product values come from the live source record, so product facts are not duplicated or fabricated in source code.

Each Golden has a stable case name, a question, expected answer text, and the expected tool name/UPC argument.

### `product_agent/evaluation/metrics.py`

`build_metrics()` creates fresh metric objects for each case. Metrics cover task completion, exact tool selection/arguments, relevance, prompt alignment, faithfulness, and business-response quality.

`async_mode=False` keeps calls serial to avoid a burst of LLM evaluation requests on this Windows setup.

### `product_agent/evaluation/cases.py`

`build_test_case(golden, result)` joins an expected Golden with its actual `AgentResult` and returns a DeepEval `LLMTestCase`. It supplies answer, expected answer, actual/expected tools, and retrieved context.

## Pytest framework

### `tests/conftest.py`

Fixtures replace TestNG-style setup/teardown:

| Fixture | Scope | Responsibility |
| --- | --- | --- |
| `settings` | `session` | One immutable configuration snapshot. |
| `evaluation_dataset` | `module` | Build Goldens once from MongoDB. |
| `agent` | `module` | Create one agent and close it reliably after the product tests. |

The `agent` fixture uses `yield`, so `agent.close()` runs during teardown even if a test fails. `conftest.py` is not a test file. Its name does not start with `test_`.

### `tests/test_product_agent.py`

Each product question is its own function:

```text
test_basic_lookup
test_size
test_category
test_classification
test_reviews
test_sourcing
test_multiple_attributes
test_summary
test_group
test_subclass_1
test_subclass_2
test_concise_size
test_unknown_upc
```

`_check_product_answer` is a helper. Pytest does not collect it. Each `test_` function calls that helper, builds an `LLMTestCase`, and calls `assert_test(...)`. A score below the limit fails that function.

### Metric example files

Each former standalone example is now a normal pytest file under `tests/`. For example, `tests/test_answer_relevancy_offline.py` defines `test_answer_relevancy_offline`. Pytest finds these files by name. Nothing loads a folder of scripts and runs them one by one.

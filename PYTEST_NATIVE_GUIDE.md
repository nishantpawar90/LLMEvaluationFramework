# Product agent evaluation framework

This is the single explanation of the project: what it is, how pytest finds a test, what the command initializes, and how one product question moves from the command line to a pass or fail. The old `CODE_WALKTHROUGH.md` and `FRAMEWORK_GUIDE.md` files only point here.

## 1. What this project is

A LangGraph agent answers product questions through a narrow MongoDB tool boundary. Pytest finds and runs the checks. DeepEval scores the answer and the tool behaviour.

```text
question -> ChatOpenAI -> one read-only tool -> MongoDB -> ChatOpenAI -> answer
```

The model receives five tools. It never receives a MongoDB client or a free-form query tool. `MongoProductRepository` owns the only database query: `find_one` by `upcId`.

## 2. Layout

```text
DeepEvalImp/
├── product_agent/
│   ├── agent.py                 # LangGraph agent and AgentResult
│   ├── config.py                # settings from the environment
│   ├── mongo_client.py          # the only MongoDB query
│   ├── tools.py                 # five read-only tools
│   ├── prompts.py               # system prompt
│   └── evaluation/
│       ├── dataset.py           # 13 questions and expected answers
│       ├── metrics.py           # DeepEval score limits
│       └── cases.py             # joins the expected answer with the agent result
├── tests/
│   ├── conftest.py              # shared setup; not a test file
│   ├── test_product_agent.py    # 13 product questions
│   └── test_*.py                # one metric example per file
├── pytest.ini
├── .env.example
└── requirements.txt
```

## 3. How pytest decides what a test is

Pytest is the program that finds tests, runs them, and reports pass or fail. You do not start a test by calling it from another script. You start pytest.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

`python -m pytest` means "run the pytest module with this project's Python." `.venv` is the environment that has pytest, DeepEval, and the agent libraries installed.

Pytest uses names. Both of these must be true:

1. The file name starts with `test_` and ends with `.py`.
2. The function name starts with `test_`.

```text
tests/test_answer_relevancy_offline.py
    def test_answer_relevancy_offline():
```

Pytest reports that function as:

```text
tests/test_answer_relevancy_offline.py::test_answer_relevancy_offline
```

The part before `::` is the file. The part after `::` is the function. That string is the node id. Pass it to pytest to run only that test.

These are not tests:

| Name | Why pytest ignores it |
| --- | --- |
| `AnswerRelevancyMetricOffline.py` | The file name does not start with `test_`. |
| `def _check_product_answer(...)` | The function name starts with `_`, not `test_`. |
| `tests/conftest.py` | Pytest loads this name for shared setup. It is not a test file. |
| `product_agent/agent.py` | It is outside `tests/`. `pytest.ini` tells pytest to look only in `tests/`. |

`_check_product_answer` in `tests/test_product_agent.py` is a helper. `test_size` is the test, and it calls the helper.

## 4. `pytest.ini`

Pytest reads `pytest.ini` from the project root on every command.

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -ra --html=pytest-report.html --self-contained-html --alluredir=allure-results --clean-alluredir
markers =
    evaluation: live product-agent evaluation requiring MongoDB and OpenAI
```

| Line | What it does |
| --- | --- |
| `testpaths = tests` | Collect tests only from `tests/`. |
| `python_files = test_*.py` | A test file name must start with `test_`. |
| `-ra` | After the run, print why each non-passing test was skipped or failed. |
| `--html=pytest-report.html` | Write the pytest-html report. |
| `--self-contained-html` | Keep the report styling inside that one file. |
| `--alluredir=allure-results` | Write Allure's raw result files. |
| `--clean-alluredir` | Empty `allure-results/` at the start of this run. |
| `markers` | Register the label `evaluation` so pytest accepts `@pytest.mark.evaluation`. |

`addopts` is applied even when you type a shorter command. `python -m pytest -q` is really pytest plus `-q` plus every option in `addopts`.

## 5. Pass, fail, and skip

Pytest calls the test function.

- The function returns normally: the test passes.
- The function raises `AssertionError`: the check failed.
- The function raises any other exception, such as `ModuleNotFoundError` or a connection error: the test also fails, and the command exits with a failure.

```python
assert result.answer != ""
```

If the answer is empty, Python raises `AssertionError`.

The product tests use DeepEval instead of that line:

```python
assert_test(test_case, metrics=build_metrics(settings), run_async=False)
```

`assert_test` scores the answer. A score below its threshold raises `AssertionError`. The message names the metric, the score, the threshold, and the reason. `run_async=False` scores one metric after another.

Some metric-example files call `evaluate(...)`. `evaluate` records a result and does not raise when a score is low, so that pytest function can still pass. The product questions use `assert_test` so a low score fails that function.

`-q` prints one character per test: `.` passed, `F` failed, `s` skipped.

## 6. Fixtures

A fixture prepares something a test needs. The test asks for it by parameter name:

```python
def test_size(agent, evaluation_dataset, settings):
    ...
```

Pytest calls the fixtures named `agent`, `evaluation_dataset`, and `settings`, then passes the results in. The fixtures live in `tests/conftest.py`. You do not import that file. Pytest loads `conftest.py` because of its name.

```python
@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="module")
def evaluation_dataset(settings: Settings):
    return build_dataset(settings)


@pytest.fixture(scope="module")
def agent(settings: Settings):
    product_agent = ProductAgent(settings)
    yield product_agent
    product_agent.close()
```

| Fixture | Scope | When it is created |
| --- | --- | --- |
| `settings` | `session` | Once for the whole pytest command. |
| `evaluation_dataset` | `module` | Once for `tests/test_product_agent.py`. All 13 product functions share it. |
| `agent` | `module` | Once for that same file. All 13 product functions share it. |

`evaluation_dataset` depends on `settings`, so pytest creates settings first.

`yield` splits setup from teardown. Code before `yield` creates the agent. The test receives that agent. Code after `yield` runs after the tests that used it, including after a failure. `product_agent.close()` closes the MongoDB client.

The metric-example files do not request these fixtures. Each of those tests creates its own `ProductAgent` inside the function. A skipped test does not trigger its fixtures. With `RUN_EVALUATIONS` unset, pytest skips every test and does not create settings, the dataset, or the agent.

## 7. Markers

```python
pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.skipif(
        os.getenv("RUN_EVALUATIONS") != "1",
        reason="Set RUN_EVALUATIONS=1 to run live MongoDB and OpenAI tests.",
    ),
]
```

`pytestmark` applies those labels to every test in the file. `evaluation` is the label registered in `pytest.ini`. This command runs only tests with that label:

```powershell
.\.venv\Scripts\python.exe -m pytest -m evaluation
```

`skipif` skips the test when `RUN_EVALUATIONS` is not `1`. A skip is not a failure. The function is not called.

## 8. The command, and what is initialized

Run one product question:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_product_agent.py::test_size -q
```

Before `test_size` runs, pytest initializes the process in this order.

**A. PowerShell.** `$env:RUN_EVALUATIONS = "1"` sets one variable for this window. The tests read it later and decide not to skip.

**B. Python from `.venv`.** `python -m pytest` starts pytest with the installed packages: pytest, pytest-html, allure-pytest, DeepEval, LangChain, LangGraph, and PyMongo.

**C. `pytest.ini`.** Pytest loads `testpaths`, the `test_*.py` rule, the `evaluation` marker, and `addopts`. `--clean-alluredir` deletes old files in `allure-results/` now, before any test.

**D. Import.** Pytest imports `tests/conftest.py` and `tests/test_product_agent.py`. Importing `product_agent.config` calls `load_dotenv()`, so values from `.env` enter the process environment. Nothing has opened MongoDB yet. `Settings()` has not been constructed yet. The agent has not been constructed yet.

**E. Collection.** Pytest reads the file and lists every `test_` function. For this command the list is only `test_size`. It evaluates `skipif`. Because `RUN_EVALUATIONS` is `1`, the test is not skipped.

**F. Session fixture `settings`.** Pytest calls `settings()` once. `Settings` reads `OPENAI_API_KEY`, `MONGODB_URI` (default `mongodb://localhost:27017`), `MONGODB_DATABASE` (default `product_agent`), `MONGODB_COLLECTION` (default `ProductUPC`), `PRODUCT_AGENT_MODEL` (default `gpt-4.1-mini`), `EVALUATION_MODEL` (default `gpt-4.1-mini`), and `PRODUCT_AGENT_SAMPLE_UPC` (default `0001960004580`). The object is frozen. It does not connect to anything.

**G. Module fixture `evaluation_dataset`.** Pytest calls `build_dataset(settings)`. That opens a MongoDB client, loads the sample UPC, turns the document into business fields, builds the 13 Goldens, and closes that client. The Goldens stay in memory for every product test in this file.

**H. Module fixture `agent`.** Pytest calls `ProductAgent(settings)`. Construction does all of this before the test function starts:

1. `require_openai()` stops if `OPENAI_API_KEY` is missing.
2. A new `MongoProductRepository` opens the MongoDB client used by the tools.
3. `make_product_tools()` builds the five read-only tools around that repository.
4. A DeepEval `CallbackHandler` is created for tracing.
5. `ChatOpenAI` is created with `temperature=0`, bound to those five tools.
6. A LangGraph `StateGraph` is compiled: `START -> agent -> tools (when the model asks) -> agent -> END`.

The fixture then `yield`s that agent. Teardown has not run yet.

**I. The test function starts.** Only now does pytest call `test_size(agent, evaluation_dataset, settings)`.

If you run the whole file instead of one function, steps F, G, and H still happen once. The 13 functions then share that dataset and that agent. After the last product test in the file, the fixture continues after `yield` and calls `agent.close()`.

If you run the whole `tests/` folder, pytest first collects all 37 tests. Metric-example files do not use these fixtures, so their agents are created inside each test function. The shared `settings`, dataset, and agent above are created when pytest reaches `tests/test_product_agent.py`.

## 9. One test, from the function to the result

`test_size` is the example. The same path applies to the other 12 product functions. Only the Golden name changes.

**J. Enter the test.**

```python
def test_size(agent, evaluation_dataset, settings):
    _check_product_answer(agent, evaluation_dataset, settings, "size")
```

Pytest does not collect `_check_product_answer`. The test calls it with the name `"size"`.

**K. Select the expected case.** The helper finds the Golden whose name is `size`. That Golden already holds the question ("What is the size of UPC ...?"), the expected size text from MongoDB, and the expected tool `get_product_dimensions` with that UPC.

**L. Ask the agent.** `agent.run(golden.input)` does the following:

1. Reject an empty question.
2. Invoke the compiled graph with two messages: the system prompt, then the human question.
3. The `agent` node calls `ChatOpenAI`. The model selects a tool. For this question that is `get_product_dimensions`.
4. `tools_condition` routes to the `tools` node.
5. The tool calls `MongoProductRepository.find_by_upc`. The repository checks the UPC, runs `find_one` on `upcId`, and returns the document. A missing product raises `ProductNotFoundError`. A connection problem becomes `ConnectionError`.
6. `product_facts()` turns the document into business fields. The tool returns that subset, not the raw document and not internal field names.
7. The graph returns to the `agent` node. The model writes the final answer from the tool output.
8. `run` reads the message list and builds an `AgentResult`: the answer text, the `ToolCall` records (name, arguments, and tool output), and `tool_context` (the tool texts).
9. DeepEval's current trace is updated with the question, the answer, and the tool calls.
10. `AgentResult` returns to the test.

**M. Build the DeepEval case.** `build_test_case(golden, result)` returns an `LLMTestCase` with:

- the question
- the agent's answer
- the expected answer
- the tools the agent called
- the tools the Golden expected
- the tool text, stored as both context and retrieval context

**N. Build the scorers.** `build_metrics(settings)` creates a fresh list. The judge model is `settings.evaluation_model`.

| Metric | Threshold | A low score means |
| --- | --- | --- |
| `TaskCompletionMetric` | 0.70 | The answer does not complete the request. |
| `ToolCorrectnessMetric` | 1.0 | The called tools are not an exact match to the expected tool, including the UPC argument. |
| `ArgumentCorrectnessMetric` | 1.0 | The tool arguments are not the expected ones. |
| `AnswerRelevancyMetric` | 0.70 | The answer drifts off the question. |
| `PromptAlignmentMetric` | 0.70 | The answer misses the instructions: be concise, do not invent facts, use only tool data, say when a product is missing, and do not expose internal field names. |
| `FaithfulnessMetric` | 0.70 | A claim is not supported by the tool output. |
| `GEval` | 0.70 | The custom business check failed: the answer should be accurate, not invented, clear, and concise. |

Threshold `1.0` means any extra or missing tool fails tool correctness. The other scores run from 0 to 1 and fail below 0.70. `async_mode=False` keeps the judge calls serial.

**O. Score.** `assert_test(...)` sends the `LLMTestCase` through each metric. Each judge call uses OpenAI.

**P. Pass or fail.** Every score at or above its threshold: `assert_test` returns, `test_size` returns, pytest records a pass. Any score below its threshold: `assert_test` raises `AssertionError`, and pytest records a failure for `test_size` only.

**Q. Teardown, if this was the last product test using the agent.** `agent.close()` closes the repository created in step H. The dataset's own MongoDB client was already closed in step G.

**R. Reports.** Pytest writes this test into `pytest-report.html` and writes a raw result file under `allure-results/`. The HTML file can be opened directly. The Allure page is a separate step, in section 12.

**S. Process exit.** Pytest exits 0 when every executed test passed. It exits 1 when any test failed.

## 10. The 13 product questions

| Function | What it asks | Expected tool |
| --- | --- | --- |
| `test_basic_lookup` | What product this UPC is. | `get_product_by_upc` |
| `test_size` | The size. | `get_product_dimensions` |
| `test_category` | The category. | `get_product_classification` |
| `test_classification` | The class. | `get_product_classification` |
| `test_reviews` | Whether the product can receive reviews. | `get_product_review_eligibility` |
| `test_sourcing` | Whether supply is DSD or warehouse. | `get_product_sourcing` |
| `test_multiple_attributes` | Name, size, and category together. | `get_product_by_upc` |
| `test_summary` | A short summary. | `get_product_by_upc` |
| `test_group` | The product group. | `get_product_classification` |
| `test_subclass_1` | The first subclass. | `get_product_classification` |
| `test_subclass_2` | The second subclass. | `get_product_classification` |
| `test_concise_size` | The size, with an instruction to be concise. | `get_product_dimensions` |
| `test_unknown_upc` | UPC `9999999999999`, which is not loaded. | `get_product_by_upc` |

`test_unknown_upc` expects the text "Product not found." The other expected answers are read from the live sample document. They are not copied into the test file.

The five tools are:

- `get_product_by_upc`
- `get_product_review_eligibility`
- `get_product_classification`
- `get_product_dimensions`
- `get_product_sourcing`

## 11. Application code, file by file

### `product_agent/config.py`

`load_dotenv()` runs when this module is imported. `Settings` is a frozen dataclass. Required runtime values are `OPENAI_API_KEY`, `MONGODB_URI`, `MONGODB_DATABASE`, and `MONGODB_COLLECTION`. `.env` is local. `.env.example` is the committed template. Production or CI should set the same names in the environment.

### `product_agent/mongo_client.py`

`MongoProductRepository` is the only database-access boundary. `find_by_upc()` validates the UPC, returns the product document, raises `ProductNotFoundError` when the UPC is absent, and converts PyMongo errors to `ConnectionError`.

### `product_agent/tools.py`

`product_facts()` normalizes a document into business fields. `make_product_tools()` exposes the five read-only LangChain tools. The model does not receive a MongoDB client.

### `product_agent/agent.py`

`ProductAgent.run(question)` returns `AgentResult`: answer, captured tool calls, and tool outputs. The graph is:

```text
START -> agent -> tools (when requested) -> agent -> END
```

`python -m product_agent.agent "What is the size of UPC 0001960004580?"` runs that path once from the command line and prints the answer. It does not run pytest and it does not score the answer.

### `product_agent/evaluation/dataset.py`

`build_dataset()` reads the sample product and creates 13 Goldens. Each Golden has a name, a question, expected answer text, and one expected tool call. Product facts come from MongoDB so the tests do not hard-code them.

### `product_agent/evaluation/metrics.py`

`build_metrics()` creates fresh metric objects for one case. `async_mode=False` avoids a burst of judge calls.

### `product_agent/evaluation/cases.py`

`build_test_case(golden, result)` joins the Golden and the `AgentResult` into one `LLMTestCase`.

## 12. Metric-example tests

Each other file in `tests/` is one metric example. The file name and the function name both start with `test_`. Pytest finds them by that rule. Nothing scans a folder and launches scripts.

| File | Function | What the name means |
| --- | --- | --- |
| `tests/test_answer_relevancy_offline.py` | `test_answer_relevancy_offline` | One `LLMTestCase`, then `evaluate`. |
| `tests/test_answer_relevancy_online.py` | `test_answer_relevancy_online` | A DeepEval dataset iterator. |
| `tests/test_argument_correctness_offline.py` | `test_argument_correctness_offline` | One live question. |
| `tests/test_argument_correctness_online.py` | `test_argument_correctness_online` | A dataset iterator. |
| `tests/test_faithfulness_offline.py` | `test_faithfulness_offline` | One live question. |
| `tests/test_faithfulness_online.py` | `test_faithfulness_online` | A dataset iterator. |
| `tests/test_tool_correctness_offline.py` | `test_tool_correctness_offline` | One live question. |
| `tests/test_tool_correctness_online.py` | `test_tool_correctness_online` | A dataset iterator. |
| `tests/test_tool_correctness_synthetic.py` | `test_tool_correctness_synthetic` | A prepared tool call. The agent is not called. |
| `tests/test_task_completion_offline.py` | `test_task_completion_offline` | One live question. |
| `tests/test_task_completion_online.py` | `test_task_completion_online` | A dataset iterator. |
| `tests/test_prompt_alignment.py` | `test_prompt_alignment` | Prompt alignment on one question. |
| `tests/test_hallucination.py` | `test_hallucination` | Hallucination on one question. |
| `tests/test_geval.py` | `test_geval` | Custom GEval for classification. |
| `tests/test_safety_bias.py` | `test_safety_bias` | Bias. |
| `tests/test_safety_jailbreak.py` | `test_safety_jailbreak` | Jailbreak prompts. |
| `tests/test_safety_pii_leakage.py` | `test_safety_pii_leakage` | PII leakage. |
| `tests/test_safety_prompt_injection.py` | `test_safety_prompt_injection` | Prompt injection. |
| `tests/test_safety_toxicity.py` | `test_safety_toxicity` | Toxicity. |
| `tests/test_safety_unsafe_output.py` | `test_safety_unsafe_output` | Unsafe-output refusal. |
| `tests/test_turn_relevancy.py` | `test_turn_relevancy` | A prepared multi-turn conversation. |
| `tests/test_knowledge_retention.py` | `test_knowledge_retention` | A prepared multi-turn conversation. |
| `tests/test_conversation_completeness.py` | `test_conversation_completeness` | A prepared multi-turn conversation. |
| `tests/test_conversational_geval.py` | `test_conversational_geval` | A live multi-turn conversation. |

"Offline" means one test case and `evaluate`. "Online" means a DeepEval dataset iterator. "Synthetic" means the inputs are prepared in the test.

These files use the same `pytestmark`, so they stay skipped until `RUN_EVALUATIONS=1`.

`test_safety_prompt_injection` and `test_safety_unsafe_output` import `deepeval.classifiers`. That module is not in DeepEval 4.1.5. Those two tests fail with `ModuleNotFoundError` before a score is computed.

This project collects 37 tests: 13 product functions plus these 24 examples.

## 13. Reports

One pytest command writes two different outputs.

### pytest-html

`pytest-report.html` appears in the project root. Open that file. It lists each test, the outcome, and the failure text.

### Allure

`allure-results/` contains raw JSON. It is not a page.

```powershell
allure generate allure-results -o allure-report --clean
allure open allure-report
```

`allure generate` writes `allure-report/index.html`. `allure open` serves that folder on localhost. Opening `index.html` from disk stays blank, because the browser will not load the report data from a `file://` path.

`--clean-alluredir` clears the raw results at the start of pytest. An old `allure-report/` folder remains until you generate again. If the page looks older than the test run, generate it again.

Allure calls an unexpected exception **broken** and a failed `assert_test` **failed**. Pytest counts both as failed. A run can show 5 pytest failures while Allure shows 3 failed and 2 broken.

`.gitignore` excludes `pytest-report.html`, `allure-results/`, and `allure-report/`.

## 14. Commands

List tests. This does not open MongoDB and does not call OpenAI. It does import the test modules, which loads `.env`.

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q
```

Safe default. All 37 tests are collected and skipped. Fixtures are not created.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Every test:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest -q
```

Only tests marked `evaluation` (in this project, that is the same 37 tests):

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest -m evaluation -q
```

One product question:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_product_agent.py::test_size -q
```

One metric example:

```powershell
$env:RUN_EVALUATIONS = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_answer_relevancy_offline.py -q
```

Ask the agent without scoring:

```powershell
.\.venv\Scripts\python.exe -m product_agent.agent "What is the size of UPC 0001960004580?"
```

MongoDB for a fresh checkout:

```powershell
.\scripts\setup_mongodb.ps1
& .\.mongodb\server\mongodb-win32-x86_64-windows-4.4.29\bin\mongod.exe `
  --dbpath .\.mongodb\data --bind_ip 127.0.0.1 --port 27017 `
  --logpath .\.mongodb\mongod.log
.\.venv\Scripts\python.exe scripts/load_product_upc.py
```

The loader upserts the sample document and creates a unique index on `upcId`. The local data directory is `.mongodb/`, and it is not committed. `ProductUPC.txt` was not in the supplied workspace, so this project does not embed a copied product document. The dataset reads the live sample document when the `evaluation_dataset` fixture runs.

## 15. Adding a product question

1. Add a Golden in `build_dataset()` with a name, question, expected answer, and expected tool.
2. Add `def test_<name>(...)` in `tests/test_product_agent.py`.
3. Call `_check_product_answer(..., "<name>")` from that function.

Pytest collects the new function because of the `test_` name. There is no separate list of files to register.

## 16. A short way to say it

`python -m pytest` reads `pytest.ini`, imports `tests/`, and collects every `test_` function. Importing config loads `.env`. With `RUN_EVALUATIONS=1`, the product file then builds one `Settings`, one dataset from MongoDB, and one `ProductAgent` with its graph and tools. `test_size` selects the size Golden, runs the agent, builds an `LLMTestCase`, and `assert_test` fails that function if any score is below its threshold. Pytest writes `pytest-report.html` and `allure-results/`. `allure generate` and `allure open` turn the raw Allure files into a page.

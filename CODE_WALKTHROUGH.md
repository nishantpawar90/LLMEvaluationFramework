# Product Information Agent: Code Walkthrough

This document explains every source file in the proof of concept and how they
work together. The project is deliberately small: MongoDB is the source of
truth, LangGraph controls the LLM/tool loop, and DeepEval evaluates the result.

## 1. End-to-end flow

```text
User question
  -> ProductAgent.run()
  -> LangGraph agent node (ChatOpenAI + system prompt)
  -> one of five controlled tools
  -> MongoProductRepository.find_by_upc()
  -> MongoDB: product_agent.ProductUPC
  -> normalized tool result
  -> LangGraph agent node writes final answer
  -> AgentResult(answer, captured tool calls, tool context)
  -> optional DeepEval evaluation
```

The model cannot execute MongoDB queries itself. It sees only the five
functions returned by `make_product_tools()`. The repository contains the one
Mongo query used by the application: `find_one({"upcId": ...})`.

## 2. Configuration and dependencies

### `requirements.txt`

The dependency versions match the local environment used to build the PoC.

| Package | Why it is present |
| --- | --- |
| `langchain`, `langchain-core` | Tool definitions, messages, and model integration. |
| `langgraph` | The explicit LLM -> tool -> LLM execution graph. |
| `langchain-openai` | `ChatOpenAI`, which invokes the OpenAI model. |
| `pymongo` | MongoDB connection, query, upsert, and index management. |
| `deepeval` | Evaluation metrics, datasets, test cases, and tracing decorators. |
| `python-dotenv` | Loads local `.env` variables into the process. |
| `portalocker[win32]` | Windows shared-lock support for DeepEval's evaluation cache. |

### `.env` and `.env.example`

`.env` is local-only configuration and is excluded by `.gitignore`. Its Mongo
settings point to the project-local server:

```dotenv
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=product_agent
MONGODB_COLLECTION=ProductUPC
PRODUCT_AGENT_SAMPLE_UPC=0001960004580
OPENAI_API_KEY=
```

Set `OPENAI_API_KEY` before running the agent or LLM-judged DeepEval metrics.
`.env.example` is the shareable template without secrets.

### `product_agent/config.py`

`load_dotenv()` reads `.env` when this module is imported. `Settings` is a
frozen dataclass, so each instance is an immutable snapshot of configuration.

- `mongodb_uri`, `mongodb_database`, and `mongodb_collection` have sensible
  local defaults. Environment variables still override them.
- `model` is the answering model and `evaluation_model` is the evaluator model.
- `sample_upc` identifies the document used to construct the Goldens.
- `require_mongodb()` checks that connection settings exist before a repository
  is created.
- `require_openai()` fails early with a clear message instead of allowing an
  OpenAI request to fail later.

## 3. MongoDB access

### `product_agent/mongo_client.py`

This file is the database boundary.

`ProductNotFoundError` is a dedicated exception. It lets callers distinguish a
valid UPC that has no matching document from a malformed UPC or a server error.

`validate_upc(upc)` performs input validation before any query:

1. Converts the value to text and strips whitespace.
2. Requires digits only.
3. Requires 13 digits, allowing UPC/EAN-like identifiers while rejecting
   accidental text or truncated IDs.
4. Returns the normalized value, preserving leading zeroes because it is a
   string, not a number.

`MongoProductRepository.__init__()` creates a `MongoClient` with a five-second
server-selection timeout and stores the configured collection. Creating a
client is lazy; the connection is verified when the first operation occurs.

`find_by_upc()` is decorated with `@observe(type="tool")`, so DeepEval can
trace it when tracing is configured. It calls:

```python
self._collection.find_one({"upcId": normalized}, {"_id": 0})
```

The first dictionary is a fixed equality filter. The second is a projection
that removes Mongo's internal `_id` field from results. No part of a user
question becomes a MongoDB operator or arbitrary filter. PyMongo exceptions
become a business-safe `ConnectionError`; no matching document becomes
`ProductNotFoundError`.

`close()` releases the client resources after an agent or dataset operation.

## 4. Prompt and fact normalization

### `product_agent/prompts.py`

`SYSTEM_PROMPT` is the model's behavioral contract. It requires tool use for
facts, prohibits invention, asks for the most specific tool for a single
attribute, defines not-found wording, requests concise business language, and
prevents exposing implementation details such as MongoDB field names.

The wording matters: it supports both good application behaviour and the
`PromptAlignmentMetric` evaluation later.

### `product_agent/tools.py`

This module does two related jobs: normalize the source document into stable
business labels and expose safe, LLM-callable tools.

#### `_value(product, *keys)`

This helper attempts each supplied dotted path in order. For example,
`"itemDimensions.size"` walks `product["itemDimensions"]["size"]` safely.
It returns the first non-empty value, otherwise `None`. This lets the PoC
support source-document variations without returning an invented fallback.

#### `product_facts(product)`

The source document is nested, whereas agent answers should use friendly names.
The mapping produces this normalized shape:

```python
{
  "product_name": "CELESTE DELUXE PIZZA",
  "brand": None,
  "size": "5.9 OZ",
  "product_group": "PREPARED FROZEN FOODS",
  "category": "PIZZA FROZEN PREPARED FOODS",
  "class": "SINGLE SERVE FROZEN PIZZA",
  "subclass_level_1": "...",
  "subclass_level_2": "...",
  "review_eligibility": True,
  "sourcing": "DSD supplied",
  "upc": "0001960004580"
}
```

For the provided document, product name comes from
`itemDesc.internetItemDsc`, size from `itemDimensions.size`, and category from
`productCategory.productCategoryNm`. Sourcing is intentionally calculated from
the two indicator fields: `dsdInd == "Y"` yields `DSD supplied`; otherwise
`warehouseInd == "Y"` yields `Warehouse supplied`. A blank `brandNm` remains
`None`, which is important: the agent is not given a made-up brand.

#### `make_product_tools(repository)`

The inner `fetch(upc)` function is shared error handling. It calls the
repository and converts expected exceptions into serializable tool results:

```python
{"found": True, "product": {...}}
{"found": False, "error": "Product not found."}
```

Each public function has both decorators:

- `@tool` converts its signature and docstring into a LangChain/OpenAI tool
  schema. The LLM therefore knows it requires one string argument, `upc`.
- `@observe(type="tool")` creates a DeepEval trace span for its invocation.

The tool boundaries are intentional:

| Tool | Returns | Intended question |
| --- | --- | --- |
| `get_product_by_upc` | All normalized facts | General lookup, summary, or multiple facts. |
| `get_product_review_eligibility` | Review eligibility only | Customer-review questions. |
| `get_product_classification` | Group/category/class/subclasses | Classification questions. |
| `get_product_dimensions` | Size only | Size/dimension questions. |
| `get_product_sourcing` | DSD/warehouse result only | Supply-method questions. |

The selective responses keep answers relevant and allow tool-selection quality
to be tested. All tools ultimately use the same safe fixed UPC lookup.

## 5. The LangGraph agent

### `product_agent/agent.py`

`AgentState` has one field: `messages`. The `add_messages` annotation tells
LangGraph to append node outputs to the existing message history rather than
overwrite it.

`AgentResult` is the application-level result returned to callers:

- `answer`: final natural-language response;
- `tool_calls`: DeepEval-compatible records of the tools the model chose;
- `tool_context`: raw tool outputs, used as evaluation grounding context.

`ProductAgent.__init__()` performs setup in this order:

1. Loads/validates settings and requires an OpenAI key.
2. Creates the Mongo repository.
3. Builds the five controlled tools using that repository.
4. Creates a deterministic (`temperature=0`) `ChatOpenAI` model and calls
   `.bind_tools(self.tools)`. Binding tools advertises only these five tools to
   OpenAI.
5. Creates and compiles the graph.

The graph has two nodes:

```text
START -> agent -> [tool call?] -> tools -> agent -> ... -> END
```

- The `agent` node calls `_call_model()`, which invokes the model with the
  accumulated messages.
- `tools_condition` examines the model response. If it contains a tool call,
  control goes to LangGraph's `ToolNode`; otherwise it goes to `END`.
- `ToolNode` executes the requested safe tool and adds a `ToolMessage` to the
  state.
- The edge from `tools` back to `agent` gives the model the tool result and lets
  it write a grounded final answer.

`run(question)` validates that the question is not empty, starts the graph with
the system prompt and a `HumanMessage`, and reads the last message as the final
answer. It then walks every message to capture tool activity:

1. AI messages contain `tool_calls` with an ID, name, and arguments.
2. A `ToolCall` record is created for each of those requests.
3. Tool messages contain the matching `tool_call_id` and output.
4. The result output is attached to the corresponding `ToolCall` and added to
   `tool_context`.

This local capture is separate from tracing. It gives evaluation code concrete
facts about the execution even when no cloud trace logging is enabled.

When invoked as `python -m product_agent.agent "..."`, the bottom block creates
the agent, runs the supplied question (or its default question), prints the
answer and captured calls as JSON, then always closes the Mongo connection.

## 6. Evaluation dataset

### `product_agent/evaluation/dataset.py`

`_present()` turns empty values into `"not available"` only for an expected
output. It does not change the Mongo data or invent a product attribute.

`build_dataset()` opens the repository, reads the configured sample document,
normalizes it through `product_facts()`, and closes the repository in `finally`.
It then builds 15 `Golden` records.

A Golden is reference data, not a live trace. Each record holds:

- a stable case name;
- an input question;
- an expected answer fragment based on the actual stored document;
- an expected `ToolCall`, including the exact `upc` argument.

The cases cover basic lookup, size, category, classification, reviews,
sourcing, multiple attributes, summary, brand/missing attribute, group and
subclasses, conciseness, grounding, and an unknown UPC. The sample document is
read at execution time so expected business values are not hardcoded or
fabricated in source code.

## 7. DeepEval metrics

### `product_agent/evaluation/metrics.py`

`PROMPT_INSTRUCTIONS` mirrors the behavioral requirements from the system
prompt. `build_metrics()` obtains the configured evaluator model and creates a
fresh metric instance list for each evaluation.

| Metric | Inputs it evaluates | Threshold | Meaning in this project |
| --- | --- | --- | --- |
| `TaskCompletionMetric` | Input and actual answer | 0.70 | Did the response complete the requested task? |
| `ToolCorrectnessMetric` | Actual vs expected tools/arguments | 1.00 | Did the model select the expected tool? Exact match is required. |
| `ArgumentCorrectnessMetric` | Actual vs expected tool arguments | 1.00 | Did the call contain the expected UPC? |
| `AnswerRelevancyMetric` | Input and actual answer | 0.70 | Is the response focused on the request? |
| `PromptAlignmentMetric` | Actual answer vs instructions | 0.70 | Does the response obey concision, grounding, and not-found rules? |
| `FaithfulnessMetric` | Actual answer vs context | 0.70 | Are claims supported by captured tool output? |
| `GEval` | Input, actual answer, context | 0.70 | Custom business-focused quality judgement. |

DeepEval's LLM-based metrics need `EVALUATION_MODEL` and `OPENAI_API_KEY`.
Scores/reasons can vary slightly because an evaluator LLM makes the judgement.
The two tool metrics use the captured structural data rather than relying only
on prose. The test case supplies both `context` and `retrieval_context`: GEval
uses the former, while Faithfulness uses the latter. Metrics run with
`async_mode=False`, and the evaluation runner uses `AsyncConfig(run_async=False)`
to keep requests serial on Windows.

## 8. Evaluation execution

### `product_agent/evaluation/test_product_agent.py`

`build_test_cases(agent, settings)` is the bridge between static Golden
expectations and live executions. For each Golden it:

1. Calls `agent.run(golden.input)`.
2. Uses the actual answer, captured tool calls, and captured tool context.
3. Combines those with the Golden's expected output and expected tools into an
   `LLMTestCase`.

`test_product_agent_evaluation()` checks the OpenAI key, creates one reusable
agent, runs all cases through `deepeval.evaluate(...)`, asserts a result was
produced, and closes the Mongo client even if a test fails. It can be run by
Pytest or directly as a Python module.

### Test cases being executed

The dataset contains 15 single-turn cases. Their expected answers are derived
from the live MongoDB document at test setup time, while the expected tool and
UPC argument are explicitly defined:

| Case | Behavior under test |
| --- | --- |
| `basic_lookup` | Return the product name for a UPC. |
| `size` | Return the product size. |
| `category` | Return the product category. |
| `classification` | Return the product class. |
| `reviews` | Return customer-review eligibility. |
| `sourcing` | Return DSD or warehouse sourcing. |
| `multiple_attributes` | Return product name, size, and category together. |
| `summary` | Produce a concise product summary. |
| `brand` | Return the brand, including the not-available behavior. |
| `group` | Return the product group. |
| `subclass_1` | Return the first subclass. |
| `subclass_2` | Return the second subclass. |
| `concise_size` | Answer a size question concisely. |
| `grounded_brand` | Do not guess a missing brand. |
| `unknown_upc` | Say `Product not found.` for an unknown UPC. |

Each case is executed live. It is not a unit test with a mocked model: the
agent calls OpenAI, LangGraph selects and invokes a controlled tool, and the
tool reads MongoDB. The resulting answer, tool calls, tool outputs, expected
answer, and expected tools are assembled into a DeepEval `LLMTestCase`.

### Execution flow and frameworks

The execution layers have separate responsibilities:

1. **Pytest** discovers `test_product_agent_evaluation()` and reports pass or
  fail. The root `test_product_agent.py` is only a convenience wrapper.
2. **DeepEval** builds and evaluates the `LLMTestCase` objects. Its metrics
  judge the answer and compare the captured tool behavior with expectations.
3. **ProductAgent** uses **LangGraph** to run `agent -> tools -> agent` until
  the model returns a final answer.
4. **LangChain/OpenAI** supplies the chat model, tool schemas, messages, and
  tool-call protocol.
5. **ToolNode** invokes one of the five controlled tools.
6. **MongoDB/PyMongo** performs the fixed `find_one` lookup by `upcId`.

The sequence is therefore:

```text
pytest
  -> test_product_agent_evaluation
  -> build_dataset: MongoDB facts -> 15 Goldens
  -> build_test_cases: run each Golden through ProductAgent
  -> LLMTestCase(answer, expected answer, tool calls, context)
  -> deepeval.evaluate
  -> seven metrics per case
  -> assert EvaluationResult is not None
```

The evaluation is configured for serial execution (`async_mode=False` on each
metric and `AsyncConfig(run_async=False)` on `evaluate`) because this Windows
setup uses DeepEval's file cache and should avoid a burst of simultaneous LLM
requests. It still makes many OpenAI calls and can take several minutes.

### Interview-ready questions and answers

**What test framework executes the tests?** Pytest executes the Python test
function. DeepEval is the evaluation framework responsible for LLM test cases
and quality metrics; it is not a replacement for pytest discovery.

**Are these unit, integration, or end-to-end tests?** They are model-assisted
end-to-end evaluation tests. They exercise OpenAI, LangGraph, the real tool
boundary, and MongoDB. They are not isolated unit tests because the model and
database are live dependencies.

**How are expected values created?** The dataset reads the configured sample
document from MongoDB and normalizes it through `product_facts()`. This avoids
duplicating product facts in the test source. The unknown-UPC case is the
intentional exception because its expected result is the not-found behavior.

**What does a test case contain?** A DeepEval `LLMTestCase` contains the input,
actual output, expected output, captured tool calls, expected tools, and tool
context. Both `context` and `retrieval_context` are populated because the
configured metrics use different fields.

**What is asserted?** The test asserts that DeepEval returns an evaluation
result. Individual quality thresholds are enforced by the configured metrics:
tool correctness and argument correctness require exact matches at `1.00`,
and the LLM-judged metrics use `0.70` thresholds.

**How is tool behavior verified?** The agent converts LangGraph tool-call
messages into DeepEval `ToolCall` records, including each tool name, UPC input,
and returned output. DeepEval compares those records with the Golden's
expected tool call.

**How do you run it?** Start MongoDB, ensure the sample document is loaded,
set `OPENAI_API_KEY`, activate the virtual environment, and run
`python -m pytest -q` or `python test_product_agent.py`.

### Root `test_product_agent.py`

This is a small convenience entry point. It imports
`test_product_agent_evaluation` so this command works from the project root:

```powershell
python test_product_agent.py
```

## 9. Product loader and local MongoDB

### `scripts/load_product_upc.py`

The supplied text file is Mongo shell-style data, not strict JSON, because it
uses expressions such as `ISODate("...")`.

`SOURCE` defaults to `D:\DT\ProductUPC.txt`. `load_document()` reads the Mongo
export, removes its leading numbered-record marker, keeps the first record,
and converts each `ISODate("timestamp")` into a JSON string before calling
`json.loads()`.

`convert_dates()` recursively walks dictionaries and lists. When its current
key is `createdDate` or `modifiedDate`, it turns that timestamp string into a
Python `datetime`, so PyMongo stores a BSON Date instead of plain text.

When executed, the loader:

1. Connects to local MongoDB and runs `ping` to fail early if the server is off.
2. Selects `product_agent.ProductUPC`.
3. Calls `replace_one({"_id": document["_id"]}, document, upsert=True)`.
   The first run inserts the document; future runs replace that same document,
   preventing duplicates.
4. Creates `uniq_upcId`, a unique index that prevents separate documents from
   sharing a UPC.
5. Reads a small projection back and prints it as verification.

### `.mongodb/`

This ignored directory contains the portable MongoDB executable, its data
files, log file, and downloaded archives. It is runtime state, not application
source code. Start the database from the project root with:

```powershell
& .\.mongodb\server\mongodb-win32-x86_64-windows-4.4.29\bin\mongod.exe `
  --dbpath .\.mongodb\data `
  --bind_ip 127.0.0.1 `
  --port 27017 `
  --logpath .\.mongodb\mongod.log
```

## 10. Practical run sequence

1. Start `mongod` with the command above and leave that terminal open.
2. Put an OpenAI key in `.env`.
3. Optionally reload the document: `python scripts/load_product_upc.py`.
4. Ask a live question:

   ```powershell
   python -m product_agent.agent "What category does UPC 0001960004580 belong to?"
   ```

5. Run all 15 evaluation cases:

   ```powershell
   python test_product_agent.py
   ```

## 11. Troubleshooting notes

- Use the project virtual environment, for example
  `& .\.venv\Scripts\python.exe -m pytest -q`; the system Python may not have
  the project dependencies installed.
- MongoDB must be running on `localhost:27017` before loading data or running
  the agent.
- The loader source file is `D:\DT\ProductUPC.txt`, not a path relative to the
  current PowerShell directory. The loader handles the file's numbered Mongo
  export records and `ISODate(...)` values.
- A real `OPENAI_API_KEY` is required for both the answering model and the
  LLM-judged evaluation metrics. The key is read from the process environment
  or local `.env`; it must not be committed or documented here.
- On Windows, `portalocker[win32]` is required so DeepEval can lock its cache.
  Without it, evaluation can fail with a `test_cases_lookup_map` error.

## 12. Intentional limitations

- This PoC has one document and one exact UPC lookup. It is not a search,
  product-catalogue, or write agent.
- The loader's source path is the supplied absolute path. If the text file is
  moved, update `SOURCE` in `scripts/load_product_upc.py` or call
  `load_document()` with a different `Path`.
- DeepEval evaluation is serial by design in this Windows setup. A full run
  makes many LLM evaluator requests and can take several minutes.
- `@observe` instruments execution. Local `AgentResult` capture is what the
  evaluation uses without needing Confident AI cloud logging.
- Live calls and LLM-judged metrics consume OpenAI API usage.

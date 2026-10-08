# Product Information Agent Evaluation PoC

This is a small AI Quality Engineering proof of concept: a LangGraph product
agent retrieves facts through controlled MongoDB tools, and DeepEval assesses
its output and tool behaviour locally.

## Architecture

`question -> ChatOpenAI -> selected read-only tool -> MongoDB -> ChatOpenAI -> response`

The graph uses LangGraph's `ToolNode`.  The model only receives five narrow,
read-only tools; it never receives a database handle or an arbitrary-query
tool. `MongoProductRepository` owns the only MongoDB query (`find_one` by
`upcId`). Tools return a business-facing, normalized subset of the document.

DeepEval tracing (`@observe`) decorates the agent and repository calls. Runtime
tool calls are also normalized into `deepeval.test_case.ToolCall` records for
the evaluation reference data; tracing and expectations remain separate.

## Metrics

| Metric | Quality dimension |
| --- | --- |
| `TaskCompletionMetric` | Whether the answer completes the request. |
| `ToolCorrectnessMetric` | Whether the selected controlled tool is expected. |
| `ArgumentCorrectnessMetric` | Whether the selected tool received the expected UPC. |
| `AnswerRelevancyMetric` | Whether the response stays on the question. |
| `PromptAlignmentMetric` | Concision, grounding, not-found, and field-name instructions. |
| `FaithfulnessMetric` | Whether claims are grounded in returned tool context. |
| `GEval` | Business clarity and product-response accuracy. |

The installed DeepEval 4.1.5 provides all of these metrics. They are
LLM-judged metrics, so their scores can vary slightly and require an OpenAI
key. `ToolCorrectnessMetric` is configured for exact tool matching and
`ArgumentCorrectnessMetric` compares the captured call with the Golden.

## Run

1. Set up and start MongoDB as described in [Local MongoDB setup](#local-mongodb-setup).
2. Copy `.env.example` to `.env` and set the connection values and OpenAI key.
3. Ensure the collection has a document whose `upcId` matches
   `PRODUCT_AGENT_SAMPLE_UPC` (the default is `0001960004580`).
4. Ask a question:

   ```powershell
   python -m product_agent.agent "What is the size of UPC 0001960004580?"
   ```

5. Run the local evaluation (15 Goldens generated from the actual MongoDB
   document, so expected values are never fabricated):

   ```powershell
   python test_product_agent.py
   # or
   pytest -q
   ```

Expected output is DeepEval's per-case metric table followed by an evaluation
summary. A passing run shows scores at or above the configured 0.70 thresholds;
the exact scores/reasons depend on the evaluator model.

`ProductUPC.txt` was not present in the supplied workspace, so this project
does not embed a copied product document or claim its individual field values.
The dataset reads the live sample document when it is built.

## Local MongoDB setup

This workspace is configured for `mongodb://localhost:27017`, database
`product_agent`, and collection `ProductUPC`. The local runtime and data files
are stored under `.mongodb/` and excluded from source control. On a fresh
checkout, install the pinned local MongoDB runtime first:

```powershell
.\scripts\setup_mongodb.ps1
```

The script downloads MongoDB 4.4.29 from MongoDB's official download host,
extracts it into `.mongodb/server/`, and creates `.mongodb/data/`. Then start
the server in a separate PowerShell window:

```powershell
& .\.mongodb\server\mongodb-win32-x86_64-windows-4.4.29\bin\mongod.exe `
  --dbpath .\.mongodb\data --bind_ip 127.0.0.1 --port 27017 `
  --logpath .\.mongodb\mongod.log
```

The supplied document can be safely loaded again (it is an upsert) with:

```powershell
python scripts/load_product_upc.py
```

The loader creates a unique index on `upcId`.

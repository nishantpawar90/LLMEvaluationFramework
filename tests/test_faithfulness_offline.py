"""Faithfulness measured on one live product question.

Pytest collects this file because the file name starts with test_.
Pytest runs test_faithfulness_offline because the function name starts with test_.
"""

import pytest
from deepeval.evaluate import evaluate
from deepeval.metrics import ToolCorrectnessMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams
from dotenv import load_dotenv
from product_agent.config import Settings
from product_agent.agent import ProductAgent

pytestmark = pytest.mark.evaluation


def test_faithfulness_offline():
    # |                  | Hallucination Metric                          | Faithfulness Metric                                 |
    # | ---------------- | --------------------------------------------- | --------------------------------------------------- |
    # | Main question    | "Is the answer factually correct?"            | "Is the answer supported by the retrieved context?" |
    # | Typical use      | General LLM evaluation                        | RAG evaluation                                      |
    # | Compare          | `actual_output` ↔ `context`                   | `actual_output` ↔ `retrieval_context`               |
    # | Focus            | Factual correctness / hallucination           | Grounding in retrieved evidence                     |
    # | Typical scenario | LLM generated an answer from provided context | RAG retrieved documents → LLM generated answer      |

    load_dotenv()
    settings = Settings()
    que = "get me the review eligibility for UPC 0001960004580?"

    # Build a test case using live ProductAgent if OPENAI key is available; otherwise use a synthetic fallback
    agent = ProductAgent()
    result = agent.run(que)
    tools_called = result.tool_calls
    expected_tools = [ToolCall(name="get_product_review_eligibility", input_parameters={"upc": settings.sample_upc})]
    test_case = LLMTestCase(input=que, actual_output=result.answer,retrieval_context=result.tool_context)

    print("OUTPUT :: " + str(result.answer))

    metric = FaithfulnessMetric(
        threshold=0.7,
        model="gpt-4o",
        include_reason=True
    )

    print("Running FaithfulnessMetric...")
    result = evaluate(test_cases=[test_case], metrics=[metric])
    print("Done. Result:")
    print(result)

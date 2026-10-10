"""Hallucination measured on one live product question.

Pytest collects this file because the file name starts with test_.
Pytest runs test_hallucination because the function name starts with test_.
"""

import pytest
from typing import cast
from deepeval.config.settings import Settings
from deepeval.evaluate import evaluate
from deepeval.metrics import AnswerRelevancyMetric, TaskCompletionMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase, ToolCall
from dotenv import load_dotenv
from product_agent.agent import ProductAgent

pytestmark = pytest.mark.evaluation


def test_hallucination():
    load_dotenv()

    settings = Settings()
    que = "What is the \"product_group\", \"category\", \"class\", \"subclass_level_1\", \"subclass_level_2\" for UPC 0001960004580?"

    # Build a test case using live ProductAgent if OPENAI key is available; otherwise use a synthetic fallback
    agent = ProductAgent()
    result = agent.run(que)
    tools_called = result.tool_calls
    test_case = LLMTestCase(input=que, actual_output=result.answer,context=result.tool_context)

    print("OUTPUT :: " + str(result.answer))

    metric = HallucinationMetric(
        threshold=0.7,
        model="gpt-4o",
        include_reason=True
    )

    print("Running HallucinationMetric...")
    result = evaluate(test_cases=[test_case], metrics=[metric])
    print("Done. Result:")
    print(result)


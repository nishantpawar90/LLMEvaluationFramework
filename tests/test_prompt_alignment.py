"""Prompt alignment measured on one live product question.

Pytest collects this file because the file name starts with test_.
Pytest runs test_prompt_alignment because the function name starts with test_.
"""

import os

import pytest
from deepeval.evaluate import evaluate
from deepeval.metrics import ToolCorrectnessMetric, FaithfulnessMetric, PromptAlignmentMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams
from dotenv import load_dotenv
from product_agent.config import Settings
from product_agent.agent import ProductAgent

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.skipif(
        os.getenv("RUN_EVALUATIONS") != "1",
        reason="Set RUN_EVALUATIONS=1 to run live MongoDB and OpenAI tests.",
    ),
]


def test_prompt_alignment():
    load_dotenv()
    settings = Settings()
    que = "get me the review eligibility for UPC 0001960004580?"

    # Build a test case using live ProductAgent if OPENAI key is available; otherwise use a synthetic fallback
    agent = ProductAgent()
    result = agent.run(que)
    tools_called = result.tool_calls
    test_case = LLMTestCase(input=que, actual_output=result.answer)

    print("OUTPUT :: " + str(result.answer))

    metric = PromptAlignmentMetric(
        threshold=0.7,
        model="gpt-4o",
        include_reason=True,prompt_instructions="Give response in a rudely manner."
    )

    print("Running PromptAlignmentMetric...")
    result = evaluate(test_cases=[test_case], metrics=[metric])
    print("Done. Result:")
    print(result)

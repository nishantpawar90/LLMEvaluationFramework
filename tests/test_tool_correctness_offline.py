"""Tool correctness measured on one live product question.

Pytest collects this file because the file name starts with test_.
Pytest runs test_tool_correctness_offline because the function name starts with test_.
"""

import pytest
from deepeval.evaluate import evaluate
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams
from dotenv import load_dotenv
from product_agent.config import Settings
from product_agent.agent import ProductAgent

pytestmark = pytest.mark.evaluation


def test_tool_correctness_offline():
    load_dotenv()
    settings = Settings()
    que = "get me the review eligibility for UPC 0001960004580?"

    # Build a test case using live ProductAgent if OPENAI key is available; otherwise use a synthetic fallback
    agent = ProductAgent()
    result = agent.run(que)
    tools_called = result.tool_calls
    expected_tools = [ToolCall(name="get_product_review_eligibility", input_parameters={"upc": settings.sample_upc})]
    test_case = LLMTestCase(input=que, tools_called=tools_called, expected_tools=expected_tools)

    print("OUTPUT :: " + str(result.answer))

    metric = ToolCorrectnessMetric(threshold=0.7, evaluation_params=[ToolCallParams.INPUT_PARAMETERS], async_mode=False, model="gpt-4o")

    print("Running ToolCorrectnessMetric...")
    result = evaluate(test_cases=[test_case], metrics=[metric])
    print("Done. Result:")
    print(result)

"""Task completion measured on one live product question.

Pytest collects this file because the file name starts with test_.
Pytest runs test_task_completion_offline because the function name starts with test_.
"""

import os

import pytest
import sys
from dotenv import load_dotenv
from deepeval.evaluate import evaluate
from deepeval.metrics import TaskCompletionMetric
from deepeval.test_case import LLMTestCase
from product_agent import agent

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.skipif(
        os.getenv("RUN_EVALUATIONS") != "1",
        reason="Set RUN_EVALUATIONS=1 to run live MongoDB and OpenAI tests.",
    ),
]


def test_task_completion_offline():
    # PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    # sys.path.insert(0, PROJECT_ROOT)



    # que = "What product is UPC 0001960004580?"
    # que = "What product is UPC 0001960004581?"
    que = "What is the \"product_group\", \"category\", \"class\", \"subclass_level_1\", \"subclass_level_2\" for UPC 0001960004580?"
    agent_instance = agent.ProductAgent()
    result = agent_instance.run(que)

    print("ACTUAL OUTPUT:")
    print(result.answer)

    print("TOOL CALLS:")
    for call in result.tool_calls:
        print(call.model_dump())

    test_case = LLMTestCase(input=que, actualOutput=result.answer)
    metric = TaskCompletionMetric(threshold=0.7, model="gpt-4o")

    evaluate(test_cases=[test_case], metrics=[metric])

"""Answer relevancy measured on one live product question.

Pytest collects this file because the file name starts with test_.
Pytest runs test_answer_relevancy_offline because the function name starts with test_.
"""

import pytest
from typing import cast
from deepeval.evaluate import evaluate
from deepeval.metrics import AnswerRelevancyMetric, TaskCompletionMetric
from deepeval.test_case import LLMTestCase
import product_agent
from product_agent.agent import ProductAgent

pytestmark = pytest.mark.evaluation


def test_answer_relevancy_offline():
    que = "What is the \"product_group\", \"category\", \"class\", \"subclass_level_1\", \"subclass_level_2\" for UPC 0001960004580?"

    product_agent_instance = ProductAgent()
    result = product_agent_instance.run(que)

    testcase = LLMTestCase(input=que, actual_output=result.answer)
    # AnswerRelevancy still pass the metric even if the mongoDB connection is not setup and no info is pulled from mongodb.
    # It says, unable to fetch info for upc 0001960004580 which is still considered as relevant answer and marked as pass with score as
    answerRelevancyMetric = AnswerRelevancyMetric(model="gpt-4o", threshold=0.7, async_mode=False, verbose_mode=True)
    taskCompletionMetric = TaskCompletionMetric(threshold=0.7, model="gpt-4o")
    evaluate(test_cases=[testcase], metrics=[answerRelevancyMetric, taskCompletionMetric])

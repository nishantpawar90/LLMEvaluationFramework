"""Answer relevancy measured through a DeepEval dataset iterator.

Pytest collects this file because the file name starts with test_.
Pytest runs test_answer_relevancy_online because the function name starts with test_.
"""

import pytest
from typing import cast
from deepeval.contextvars import get_current_golden
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.evaluate import evaluate
from deepeval.metrics import AnswerRelevancyMetric, TaskCompletionMetric
from deepeval.test_case import LLMTestCase
from deepeval.tracing import observe, update_current_trace
import product_agent
from product_agent.agent import ProductAgent

pytestmark = pytest.mark.evaluation


def test_answer_relevancy_online():
    @observe(name="run")
    def run(user_input: str) -> str:
        golden = get_current_golden()
        if golden:
            if golden.expected_tools:
                update_current_trace(expected_tools=golden.expected_tools)
            if golden.expected_output:
                update_current_trace(expected_output=golden.expected_output)
        agent = ProductAgent()
        try:
            result = agent.run(user_input)
            return result.answer
        finally:
            agent.close()

    que = "What is the \"product_group\", \"category\", \"class\", \"subclass_level_1\", \"subclass_level_2\" for UPC 0001960004580?"

    answerRelevancyMetric = AnswerRelevancyMetric(model="gpt-4o", threshold=0.7, async_mode=False, verbose_mode=True)

    dataSet = EvaluationDataset(goldens=[
        Golden(input=que)
    ])

    for golden in dataSet.evals_iterator(metrics=[answerRelevancyMetric]):
        print(golden)
        run(golden.input)



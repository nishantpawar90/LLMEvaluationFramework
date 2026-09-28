import os
import sys

from deepeval.contextvars import get_current_golden
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.tracing import observe, update_current_trace
from dotenv import load_dotenv

# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
# sys.path.insert(0, PROJECT_ROOT)

from deepeval.evaluate import evaluate
from deepeval.metrics import TaskCompletionMetric
from deepeval.test_case import LLMTestCase

from product_agent.agent import ProductAgent

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



taskCompletionMetric = TaskCompletionMetric(threshold=0.5, model="gpt-4o")

dataSet = EvaluationDataset(goldens=[
    Golden(input="What is the \"product_group\", \"category\", \"class\", \"subclass_level_1\", \"subclass_level_2\" for UPC 0001960004580?"),
    Golden(input= "What product is UPC 0001960004580?"),
    Golden(input= "Get me the size dimensions for  UPC 0004122098765?")
])

for golden in dataSet.evals_iterator(metrics=[taskCompletionMetric]):
    print(golden)
    run(golden.input)
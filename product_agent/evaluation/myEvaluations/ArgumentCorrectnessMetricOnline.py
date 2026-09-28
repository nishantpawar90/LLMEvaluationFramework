from deepeval.contextvars import get_current_golden
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.evaluate import evaluate
from deepeval.metrics import ToolCorrectnessMetric, ArgumentCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams
from deepeval.tracing import update_current_trace, observe
from dotenv import load_dotenv

from product_agent.config import Settings
from product_agent.agent import ProductAgent

load_dotenv()


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


argumentCorrectnessMetric = ArgumentCorrectnessMetric(threshold=0.7, async_mode=False, model="gpt-4o",
                                                      verbose_mode=True)

que = ""
dataSet = EvaluationDataset(goldens=[
    Golden(input="get me the review eligibility for UPC 5551111043210?")
])

for golden in dataSet.evals_iterator(metrics=[argumentCorrectnessMetric]):
    print(golden)
    run(golden.input)

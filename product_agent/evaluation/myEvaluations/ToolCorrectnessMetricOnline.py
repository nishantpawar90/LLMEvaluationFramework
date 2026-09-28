from deepeval.contextvars import get_current_golden
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import ToolCall
from deepeval.tracing import observe, update_current_trace

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
        # update_current_trace(output=result.answer, tools_called=result.tool_calls)
        return result.answer
    finally:
        agent.close()


toolCorrectness = ToolCorrectnessMetric(threshold=0.7, async_mode=False)

dataSet = EvaluationDataset(goldens=[
    Golden(
        input="Get whether a product is warehouse or DSD supplied for UPC 0001960004580??",
        expected_tools=[ToolCall(name="get_product_sourcing", input_parameters={"upc": "0001960004580"})],
    )
])
for golden in dataSet.evals_iterator(metrics=[toolCorrectness]):
    print(golden)
    run(golden.input)

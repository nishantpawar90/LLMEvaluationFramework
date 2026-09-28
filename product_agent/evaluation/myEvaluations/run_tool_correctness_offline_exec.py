from deepeval.evaluate import evaluate
from deepeval.metrics.tool_correctness.tool_correctness import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams

# Construct a synthetic test case that mimics ProductAgent behaviour without calling OpenAI or Mongo
que = "What product is UPC 0001960004580?"

tools_called = [
    ToolCall(name="get_product_by_upc", input_parameters={"upc": "0001960004580"}, output={"found": True})
]
expected_tools = [
    ToolCall(name="get_product_by_upc", input_parameters={"upc": "0001960004580"})
]

testCase = LLMTestCase(
    input=que,
    actual_output="Sample answer about the product.",
    tools_called=tools_called,
    expected_tools=expected_tools,
)

# Evaluate using ToolCorrectnessMetric without needing an external model (async_mode=False)
metric = ToolCorrectnessMetric(threshold=0.7, evaluation_params=[ToolCallParams.INPUT_PARAMETERS], async_mode=False, model=None)

print("Running ToolCorrectnessMetric on synthetic test case...")
result = evaluate(test_cases=[testCase], metrics=[metric])
print("Done. Result:")
print(result)

from deepeval.evaluate import evaluate
from deepeval.metrics import ToolCorrectnessMetric, ArgumentCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams
from dotenv import load_dotenv

from product_agent.config import Settings
from product_agent.agent import ProductAgent

load_dotenv()

que = "get me the review eligibility for UPC 0001111043210?"

argumentCorrectnessMetric = ArgumentCorrectnessMetric(threshold=0.7, async_mode=False, model="gpt-4o",
                                                      verbose_mode=True)

# Build a test case using live ProductAgent if OPENAI key is available; otherwise use a synthetic fallback
agent = ProductAgent()
result = agent.run(que)
actual_tools_called = result.tool_calls
testcase = LLMTestCase(input=que,
                       tools_called=actual_tools_called, actual_output=result.answer)

print("OUTPUT :: " + str(result.answer))

print("Running ArgumentCorrectnessMetric...")
result = evaluate(test_cases=[testcase], metrics=[argumentCorrectnessMetric])

print("Done. Result:")
print(result)

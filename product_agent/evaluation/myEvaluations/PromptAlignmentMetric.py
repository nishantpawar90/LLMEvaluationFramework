from deepeval.evaluate import evaluate
from deepeval.metrics import ToolCorrectnessMetric, FaithfulnessMetric, PromptAlignmentMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams
from dotenv import load_dotenv

from product_agent.config import Settings
from product_agent.agent import ProductAgent

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

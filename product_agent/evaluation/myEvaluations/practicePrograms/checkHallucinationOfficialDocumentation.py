from deepeval.metrics import HallucinationMetric
from deepeval.test_case import LLMTestCase
from deepeval import evaluate

# Replace this with the actual documents that you are passing as input to your LLM.
context=["A man with blond-hair, and a brown shirt drinking out of a public water fountain."]

# Replace this with the actual output from your LLM application
actual_output="A blond drinking water in public."

test_case = LLMTestCase(
    input="What was the blond doing?",
    actual_output=actual_output,
    context=context
)
metric = HallucinationMetric(threshold=0.5)

# To run metric as a standalone
metric.measure(test_case)
print(metric.score, metric.reason)

evaluate(test_cases=[test_case], metrics=[metric])
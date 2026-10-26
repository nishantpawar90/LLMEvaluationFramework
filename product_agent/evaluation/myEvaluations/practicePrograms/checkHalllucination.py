from deepeval import evaluate, test_case
from deepeval.test_case import LLMTestCase
from deepeval.metrics import HallucinationMetric

testCase = LLMTestCase(
    input="What is the capital of India?",
    actual_output="The capital of India is Mumbai.",
    context=["The capital of India is Delhi"]
)

my_metric = HallucinationMetric(
    threshold=0.5,
    model="gpt-4o"
)

my_metric.measure(testCase)

print("Score:", my_metric.score)
print("Reason:", my_metric.reason)
print("Passed:", my_metric.is_successful())
evaluate(test_cases=[testCase], metrics=[my_metric])



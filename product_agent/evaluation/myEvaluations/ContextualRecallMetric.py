from deepeval.metrics import ContextualRecallMetric
from deepeval.test_case import LLMTestCase
from deepeval import evaluate

test_case = LLMTestCase(
    input="Which jam has the lowest sugar content?",
    actual_output="Berry Jam has the lowest sugar content.",
    expected_output=(
        "Berry Jam has the lowest sugar content, "
        "with 5 g per serving. "
        "Apple Jam contains 8 g per serving."
    ),
    retrieval_context=[
        "Berry Jam contains 5 g of sugar per serving."
    ]
)

metric = ContextualRecallMetric(
    threshold=0.7,
    include_reason=True
)

metric.measure(test_case)
print(metric.score, metric.reason)

evaluate(
    test_cases=[test_case],
    metrics=[metric]
)
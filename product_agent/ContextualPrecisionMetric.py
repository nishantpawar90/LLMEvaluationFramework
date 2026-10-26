from deepeval.metrics import ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase
from deepeval import evaluate

test_case = LLMTestCase(
    input="Which jam has the lowest sugar content?",
    actual_output="Berry Jam has the lowest sugar content.",
    expected_output="Berry Jam has the lowest sugar content.",
    retrieval_context=[
        "Jam is a fruit preserve available in several flavors.",
        "Berry Jam contains 5 g of sugar per serving.",
        "Apple Jam contains 8 g of sugar per serving."
    ]
)

metric = ContextualPrecisionMetric(
    threshold=0.7,
    include_reason=True
)

metric.measure(test_case)
print(metric.score, metric.reason)

evaluate(
    test_cases=[test_case],
    metrics=[metric]
)
"""Pytest-native live DeepEval coverage for the product agent."""

import os

import pytest
from deepeval import assert_test

from product_agent.evaluation.cases import build_test_case
from product_agent.evaluation.metrics import build_metrics


GOLDEN_NAMES = [
    "basic_lookup",
    "size",
    "category",
    "classification",
    "reviews",
    "sourcing",
    "multiple_attributes",
    "summary",
    "brand",
    "group",
    "subclass_1",
    "subclass_2",
    "concise_size",
    "grounded_brand",
    "unknown_upc",
]


@pytest.mark.evaluation
@pytest.mark.parametrize("golden_name", GOLDEN_NAMES)
@pytest.mark.skipif(
    os.getenv("RUN_EVALUATIONS") != "1",
    reason="Set RUN_EVALUATIONS=1 to run live MongoDB/OpenAI evaluations.",
)
def test_product_agent_meets_quality_thresholds(agent, golden, settings):
    """Run one Golden through the live agent and enforce every metric threshold."""
    result = agent.run(golden.input)
    test_case = build_test_case(golden, result)

    assert_test(test_case, metrics=build_metrics(settings), run_async=False)

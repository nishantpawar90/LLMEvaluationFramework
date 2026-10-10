"""Turn relevancy for a prepared product conversation.

Pytest collects this file because the file name starts with test_.
Pytest runs test_turn_relevancy because the function name starts with test_.
"""

import pytest
from deepeval import evaluate
from deepeval.metrics import TurnRelevancyMetric
from deepeval.test_case import Turn, ConversationalTestCase

pytestmark = pytest.mark.evaluation


def test_turn_relevancy():
    test_case = ConversationalTestCase(
        name="turn-relevancy-product-test",

        turns=[
            Turn(
                role="user",
                content="I am looking for a frozen pizza."
            ),

            Turn(
                role="assistant",
                content="Sure, I can help you find frozen pizza products."
            ),

            Turn(
                role="user",
                content="I need the product details for UPC 0001960004580."
            ),

            Turn(
                role="assistant",
                content=(
                    "The product belongs to PREPARED FROZEN FOODS "
                    "and is a SINGLE SERVE FROZEN PIZZA."
                )
            ),
            Turn(
                role="user",
                content="I need product details for UPC 0001960004580."
            ),
            Turn(
                role="assistant",
                content=(
                    "The weather in Pune is pleasant today."
                )
            ),
        ]
    )
    metric = TurnRelevancyMetric(
        threshold=0.7,
        model="gpt-4o",
        include_reason=True,
        async_mode=False,
        verbose_mode=True
    )


    print("Running TurnRelevancyMetric...")

    result = evaluate(
        test_cases=[test_case],
        metrics=[metric],
        identifier="Turn Relevancy Product Test"
    )


    print("\nDone.")
    print(result)

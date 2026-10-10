"""Conversation completeness for a prepared product conversation.

Pytest collects this file because the file name starts with test_.
Pytest runs test_conversation_completeness because the function name starts with test_.
"""

import os

import pytest
from deepeval import evaluate
from deepeval.metrics import KnowledgeRetentionMetric, ConversationCompletenessMetric
from deepeval.test_case import Turn, ConversationalTestCase

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.skipif(
        os.getenv("RUN_EVALUATIONS") != "1",
        reason="Set RUN_EVALUATIONS=1 to run live MongoDB and OpenAI tests.",
    ),
]


def test_conversation_completeness():
    # ---------------------------------------------------------
    # Conversation
    # ---------------------------------------------------------

    test_case = ConversationalTestCase(
        name="Product Agent - Knowledge Retention",

        turns=[
            Turn(
                role="user",
                content=(
                    "The product with UPC 0001960004580 belongs to "
                    "the PREPARED FROZEN FOODS product group and its "
                    "category is PIZZA FROZEN PREPARED FOODS. "
                    "Please remember these details."
                )
            ),

            Turn(
                role="assistant",
                content=(
                    "Sure. I'll remember that UPC 0001960004580 belongs "
                    "to PREPARED FROZEN FOODS and its category is "
                    "PIZZA FROZEN PREPARED FOODS."
                )
            ),

            Turn(
                role="user",
                content="What product group does this product belong to?"
            ),

            Turn(
                role="assistant",
                content=(
                    "The product belongs to PREPARED FROZEN FOODS."
                )
            ),

            Turn(
                role="user",
                content="And what category does it belong to?"
            ),

            Turn(
                role="assistant",
                content=(
                    "The product belongs to PIZZA FROZEN PREPARED FOODS."
                )
            ),
        ]
    )

    # ---------------------------------------------------------
    # Knowledge Retention Metric
    # ---------------------------------------------------------

    metric = ConversationCompletenessMetric(
        threshold=0.7,
        model="gpt-4o",
        include_reason=True,
        async_mode=False,
        verbose_mode=True
    )

    # ---------------------------------------------------------
    # Evaluate
    # ---------------------------------------------------------

    print("Running KnowledgeRetentionMetric...")

    result = evaluate(
        test_cases=[test_case],
        metrics=[metric],
        identifier="ConversationCompletenessMetric  - Product Agent"
    )

    print("\nDone.")
    print(result)

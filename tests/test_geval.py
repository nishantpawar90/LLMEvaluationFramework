"""Custom GEval score for product classification.

Pytest collects this file because the file name starts with test_.
Pytest runs test_geval because the function name starts with test_.
"""

import pytest
from deepeval.evaluate import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
from dotenv import load_dotenv
from product_agent.agent import ProductAgent

pytestmark = pytest.mark.evaluation


def test_geval():
    load_dotenv()

    # ---------------------------------------------------------
    # Input
    # ---------------------------------------------------------

    que = (
        'What is the "product_group", "category", "class", '
        '"subclass_level_1", "subclass_level_2" '
        'for UPC 0001960004580?'
    )

    # ---------------------------------------------------------
    # Run Product Agent
    # ---------------------------------------------------------

    agent = ProductAgent()

    result = agent.run(que)

    print("ACTUAL OUTPUT ::")
    print(result.answer)

    # ---------------------------------------------------------
    # Expected Output
    # ---------------------------------------------------------

    expected_answer = (
        "UPC 0001960004580, product classification \n"
        "Product Group -PREPARED FROZEN FOODS\n"
        "Category- PIZZA FROZEN PREPARED FOODS\n"
        "Class- SINGLE SERVE FROZEN PIZZA\n"
        "Subclass Level 1- VALUE SINGLE SERVE FROZEN PIZZA\n"
        "Subclass Level 2- CELESTE VALUE SINGLE SRVE FR PIZZA"
    )

    # ---------------------------------------------------------
    # Create LLM Test Case
    # ---------------------------------------------------------

    test_case = LLMTestCase(
        input=que,
        actual_output=result.answer,
        expected_output=expected_answer
    )

    # ---------------------------------------------------------
    # GEval
    # ---------------------------------------------------------

    metric = GEval(
        name="Product Classification Correctness",
        criteria=(
            "Determine whether the actual output correctly answers the user's "
            "product classification request. Compare the actual output against "
            "the expected output. The product_group, category, class, "
            "subclass_level_1, and subclass_level_2 values must be factually "
            "correct. Minor differences in wording, formatting, capitalization, "
            "or ordering should be accepted. Missing, incorrect, or fabricated "
            "classification values should reduce the score."
        ),
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT
        ],

        threshold=0.7,
        model="gpt-4o",
        async_mode=False
    )

    # ---------------------------------------------------------
    # Evaluate
    # ---------------------------------------------------------

    print("\nRunning GEval...")

    evaluation_result = evaluate(
        test_cases=[test_case],
        metrics=[metric]
    )

    print("\nDone. Result:")
    print(evaluation_result)

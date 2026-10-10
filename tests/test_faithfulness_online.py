"""Faithfulness measured through a DeepEval dataset iterator.

Pytest collects this file because the file name starts with test_.
Pytest runs test_faithfulness_online because the function name starts with test_.
"""

import os

import pytest
from deepeval.contextvars import get_current_golden
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.evaluate import evaluate
from deepeval.metrics import FaithfulnessMetric
from deepeval.tracing import observe, update_current_trace
from dotenv import load_dotenv
from product_agent.agent import ProductAgent

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.skipif(
        os.getenv("RUN_EVALUATIONS") != "1",
        reason="Set RUN_EVALUATIONS=1 to run live MongoDB and OpenAI tests.",
    ),
]


def test_faithfulness_online():
    load_dotenv()





    # ---------------------------------------------------------
    # Run the Product Agent
    # ---------------------------------------------------------
    @observe(name="run")
    def run(user_input: str):
        golden = get_current_golden()
        agent = ProductAgent()
        try:
            # ---------------------------------------------
            # Execute the actual agent
            # ---------------------------------------------
            result = agent.run(user_input)
            # ---------------------------------------------
            # Update the TOP-LEVEL DeepEval trace
            # ---------------------------------------------
            #
            # These are the values produced by the CURRENT
            # agent execution.
            #
            update_current_trace(
                input=user_input,
                output=result.answer,
                retrieval_context=result.tool_context,
                tools_called=result.tool_calls,
            )
            # ---------------------------------------------
            # Add expected values from Golden, if available
            # ---------------------------------------------
            if golden:

                if golden.expected_output:
                    update_current_trace(
                        expected_output=golden.expected_output
                    )

                if golden.expected_tools:
                    update_current_trace(
                        expected_tools=golden.expected_tools
                    )
            return result
        finally:
            agent.close()


    # ---------------------------------------------------------
    # Faithfulness Metric
    # ---------------------------------------------------------
    metric = FaithfulnessMetric(
        threshold=0.7,
        model="gpt-4o",
        include_reason=True,
        async_mode=False,
        verbose_mode=True,
    )

    # ---------------------------------------------------------
    # Evaluation Dataset
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    #
    # We do NOT execute the agent here.
    #
    # We only define the user questions.
    #
    # The actual retrieval_context will come from the
    # CURRENT agent execution inside run().
    #
    # ---------------------------------------------------------

    dataSet = EvaluationDataset(
        goldens=[
            Golden(
                input="get me the review eligibility for UPC 0001111043210?"
            ),

            Golden(
                input=(
                    'What is the "product_group", "category", "class", '
                    '"subclass_level_1", "subclass_level_2" '
                    "for UPC 0001960004580?"
                )
            ),
        ]
    )

    # ---------------------------------------------------------
    # Run Evaluation
    # ---------------------------------------------------------

    for golden in dataSet.evals_iterator(metrics=[metric]):
        print("\n")
        print("=" * 80)
        print("GOLDEN")
        print("=" * 80)

        print(f"Input: {golden.input}")

        # Execute the agent.
        #
        # This execution creates the trace containing:
        #   input
        #   output
        #   retrieval_context
        #   tools_called
        #
        run(golden.input)

        print("=" * 80)

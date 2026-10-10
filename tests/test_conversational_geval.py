"""Conversational GEval for a live product conversation.

Pytest collects this file because the file name starts with test_.
Pytest runs test_conversational_geval because the function name starts with test_.
"""

import os

import pytest
from deepeval import evaluate
from deepeval.metrics import ConversationalGEval
from deepeval.test_case import ConversationalTestCase, MultiTurnParams, Turn
from dotenv import load_dotenv
from product_agent.agent import ProductAgent
from product_agent.config import Settings

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.skipif(
        os.getenv("RUN_EVALUATIONS") != "1",
        reason="Set RUN_EVALUATIONS=1 to run live MongoDB and OpenAI tests.",
    ),
]


def test_conversational_geval():
    load_dotenv()


    # ---------------------------------------------------------
    # Create Product Agent
    # ---------------------------------------------------------

    settings = Settings()
    agent = ProductAgent(settings)


    # ---------------------------------------------------------
    # Chat function
    # ---------------------------------------------------------

    def chat(user_msg, history):

        result = agent.run(user_msg)

        # ProductAgent.run() returns AgentResult
        reply = result.answer

        # Maintain history for the conversation
        history.append({
            "role": "user",
            "content": user_msg
        })

        history.append({
            "role": "assistant",
            "content": reply
        })

        return reply, history, None


    # ---------------------------------------------------------
    # Build conversation
    # ---------------------------------------------------------

    turns = []
    history = []

    for user_msg in [
        "What is the size of UPC 0001960004580?",
        "What category is it in?",
        "What was the size you just mentioned?",
        "And what class is it?"
    ]:

        reply, history, _ = chat(user_msg, history)

        turns.append(
            Turn(
                role="user",
                content=user_msg
            )
        )

        turns.append(
            Turn(
                role="assistant",
                content=reply
            )
        )


    # ---------------------------------------------------------
    # Conversational GEval
    # ---------------------------------------------------------

    correctness = ConversationalGEval(
        name="Product Conversation Correctness",

        criteria=(
            "Did the product assistant correctly handle the entire "
            "conversation? It should use MongoDB tools when needed, "
            "provide accurate product information, maintain the product "
            "context across turns, and correctly use information from "
            "previous turns."
        ),

        model="gpt-4o",

        threshold=0.80,

        evaluation_params=[
            MultiTurnParams.ROLE,
            MultiTurnParams.CONTENT,
        ]
    )


    # ---------------------------------------------------------
    # Conversational Test Case
    # ---------------------------------------------------------

    test_case = ConversationalTestCase(
        turns=turns
    )


    # ---------------------------------------------------------
    # Evaluate
    # ---------------------------------------------------------

    evaluate(
        test_cases=[test_case],
        metrics=[correctness]
    )

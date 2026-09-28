from __future__ import annotations

from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig
from deepeval.test_case import LLMTestCase

from ..agent import ProductAgent
from ..config import Settings
from .dataset import build_dataset
from .metrics import build_metrics


def build_test_cases(agent: ProductAgent, settings: Settings):
    dataset = build_dataset(settings)
    cases = []
    for golden in dataset.goldens:
        result = agent.run(golden.input)
        cases.append(LLMTestCase(input=golden.input, actual_output=result.answer,
            expected_output=golden.expected_output, context=result.tool_context,
            retrieval_context=result.tool_context,
            tools_called=result.tool_calls, expected_tools=golden.expected_tools, name=golden.name))
    return cases


def test_product_agent_evaluation():
    settings = Settings()
    settings.require_openai()
    agent = ProductAgent(settings)
    try:
        result = evaluate(
            build_test_cases(agent, settings),
            metrics=build_metrics(settings),
            async_config=AsyncConfig(run_async=False),
        )
        assert result is not None
    finally:
        agent.close()


if __name__ == "__main__":
    test_product_agent_evaluation()

"""Create DeepEval test cases from a Golden and a live agent result."""

from deepeval.test_case import LLMTestCase

from ..agent import AgentResult


def build_test_case(golden, result: AgentResult) -> LLMTestCase:
    """Combine one expected Golden with its actual ProductAgent execution."""
    return LLMTestCase(
        name=golden.name,
        input=golden.input,
        actual_output=result.answer,
        expected_output=golden.expected_output,
        context=result.tool_context,
        retrieval_context=result.tool_context,
        tools_called=result.tool_calls,
        expected_tools=golden.expected_tools,
    )

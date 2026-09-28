from deepeval.metrics import (
    AnswerRelevancyMetric, ArgumentCorrectnessMetric, FaithfulnessMetric, GEval,
    PromptAlignmentMetric, TaskCompletionMetric, ToolCorrectnessMetric,
)
from deepeval.test_case import SingleTurnParams, ToolCallParams

from ..config import Settings

PROMPT_INSTRUCTIONS = [
    "Be concise and business-friendly.", "Do not invent product information.",
    "Only answer using information returned by tools.", "Clearly say when a product is not found.",
    "Do not expose internal MongoDB field names unless explicitly requested.",
]


def build_metrics(settings: Settings | None = None):
    model = (settings or Settings()).evaluation_model
    return [
          TaskCompletionMetric(threshold=0.70, model=model, async_mode=False),
          ToolCorrectnessMetric(threshold=1.0, evaluation_params=[ToolCallParams.INPUT_PARAMETERS], should_exact_match=True, async_mode=False),
          ArgumentCorrectnessMetric(threshold=1.0, model=model, async_mode=False),
          AnswerRelevancyMetric(threshold=0.70, model=model, async_mode=False),
          PromptAlignmentMetric(PROMPT_INSTRUCTIONS, threshold=0.70, model=model, async_mode=False),
          FaithfulnessMetric(threshold=0.70, model=model, async_mode=False),
        GEval(name="Product business response quality", threshold=0.70, model=model,
              async_mode=False,
              evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.CONTEXT],
              criteria="Evaluate whether the assistant accurately answers the product question using retrieved context, does not invent product facts, and communicates clearly and concisely for a business user."),
    ]

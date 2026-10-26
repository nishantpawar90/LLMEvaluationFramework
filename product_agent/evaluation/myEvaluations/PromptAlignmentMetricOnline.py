from deepeval.contextvars import get_current_golden
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.metrics import PromptAlignmentMetric
from deepeval.tracing import observe, update_current_trace
from dotenv import load_dotenv

from product_agent.agent import ProductAgent

load_dotenv()

PROMPT_INSTRUCTIONS = [
    "Be concise and business-friendly.",
    "Do not invent product information.",
    "Only answer using information returned by tools.",
    "Clearly say when a product is not found.",
    "Do not expose internal MongoDB field names unless explicitly requested.",
]


@observe(name="run")
def run(user_input: str) -> str:
    golden = get_current_golden()
    if golden:
        if golden.expected_tools:
            update_current_trace(expected_tools=golden.expected_tools)
        if golden.expected_output:
            update_current_trace(expected_output=golden.expected_output)

    agent = ProductAgent()
    try:
        result = agent.run(user_input)
        update_current_trace(
            input=user_input,
            output=result.answer,
            retrieval_context=result.tool_context,
            tools_called=result.tool_calls,
        )
        return result.answer
    finally:
        agent.close()


promptAlignmentMetric = PromptAlignmentMetric(
    prompt_instructions=PROMPT_INSTRUCTIONS,
    threshold=0.7,
    model="gpt-4o",
    include_reason=True,
    async_mode=False,
    verbose_mode=True,
)


dataSet = EvaluationDataset(
    goldens=[
        Golden(input="What is the product name for UPC 0001960004580?"),
        Golden(input="Get me the review eligibility for UPC 0001960004580?"),
        Golden(input="What product is UPC 9999999999999?"),
    ]
)

for golden in dataSet.evals_iterator(metrics=[promptAlignmentMetric]):
    print(golden)
    run(golden.input)

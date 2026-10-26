from deepeval.synthesizer import Synthesizer
from deepeval.dataset import EvaluationDataset, Golden

synthesizer = Synthesizer()

existing_goldens = [
    Golden(
        input="Which jam has the lowest sugar?",
        expected_output="Blueberry Jam has 4g of sugar.",
        context=[
            "Blueberry Jam contains 4g of sugar per serving.",
            "Strawberry Jam contains 8g of sugar per serving."
        ]
    )
]

new_goldens = synthesizer.generate_goldens_from_goldens(
    goldens=existing_goldens,
    max_goldens_per_golden=2,
    include_expected_output=True
)



for golden in new_goldens:
    print(golden.input)
    print(golden.expected_output)
from deepeval.synthesizer import Synthesizer
from deepeval.dataset import EvaluationDataset, Golden

synthesizer = Synthesizer()



new_goldens = synthesizer.generate_goldens_from_contexts(
    contexts=[
        ["The Earth revolves around the Sun.", "Planets are celestial bodies."],
        ["Water freezes at 0 degrees Celsius.", "The chemical formula for water is H2O."],
    ],

max_goldens_per_context=5,
    include_expected_output=True
)



for golden in new_goldens:
    print("Input:: "+golden.input)
    print("Expected Output::"+golden.expected_output)
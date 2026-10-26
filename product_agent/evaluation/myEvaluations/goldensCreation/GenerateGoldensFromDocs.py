from deepeval.synthesizer import Synthesizer
from deepeval.dataset import EvaluationDataset

synthesizer = Synthesizer()

goldens = synthesizer.generate_goldens_from_docs(
    document_paths=["capital.txt"],
    include_expected_output=True, max_goldens_per_context=4
)

dataset = EvaluationDataset(goldens=goldens)

print(len(dataset.goldens))

for golden in dataset.goldens:
    print("Question:", golden.input)
    print("Expected:", golden.expected_output)
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import LLMTestCase

# 1st way
dataset = EvaluationDataset(goldens=[Golden(input="What is capital of India?", actual_output="New Delhi")], )
print(dataset._multi_turn)
dataset.add_golden(Golden(input="What is capital of France?", actual_output="The capital of France is Paris."))
for data in dataset.goldens:
    print(data.input)
    print(data.actual_output)

print("##################")
# 2nd way
for golden in dataset.goldens:
    test_case = LLMTestCase(
        input=golden.input,
        actual_output="dfdsfd" # replace with your LLM app
    )
    dataset.add_test_case(test_case)
print(dataset.test_cases) # print to santiy check yourself

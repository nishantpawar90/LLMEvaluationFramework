expected_answers = [
    "New Delhi",
    "Mumbai",
    "Paris",
    "Tokyo",
    "London"
]

actual_answers = [
    "New Delhi",
    "Pune",
    "Paris",
    "Osaka",
    "London"
]

# Your task: Write Python code to calculate and print:
# 1. The total number of answers.
# 2. The number of incorrect answers.
# 3. The percentage of incorrect answers.
correct = 0
incorrect = 0
for expected, actual in zip(expected_answers, actual_answers):
    if expected == actual:
        print(f"Correct: {actual}")
        correct += 1
    else:
        print(f"Incorrect: Expected {expected}, but got {actual}")
        incorrect += 1


print(f"{incorrect}/{correct+incorrect}")
print(incorrect/(correct+incorrect))
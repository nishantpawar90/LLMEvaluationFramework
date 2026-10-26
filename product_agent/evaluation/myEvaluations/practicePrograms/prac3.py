evaluations = [
    {"id": "AI01", "expected": "New Delhi", "actual": "New Delhi"},
    {"id": "AI02", "expected": "Paris", "actual": "London"},
    {"id": "AI03", "expected": "Tokyo", "actual": "Tokyo"},
    {"id": "AI04", "expected": "Rome", "actual": "Milan"}
]

# Your task:
# 1. Iterate through evaluations.
# 2. Compare expected with actual.
# 3. Print the ID of each incorrect answer.
# 4. Count the incorrect answers.
# 5. Calculate the incorrect-answer percentage.
failed =0

for evals in evaluations:
    if evals['expected']==evals['actual']:
        print(f"Correct: {evals['id']}")
    else:
        print(f"Incorrect: {evals['id']}")
        failed +=1


incorrect_percentage = (failed / len(evaluations)) * 100
print(f"Incorrect-answer percentage: {incorrect_percentage:.1f}%")
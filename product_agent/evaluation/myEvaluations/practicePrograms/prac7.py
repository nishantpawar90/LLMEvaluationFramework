expected_answers = [
    "New Delhi",
    "Paris",
    "Tokyo",
    "London"
]

actual_answers = [
    "New Delhi",
    "London",
    "Tokyo",
    "London"
]
# Write a function called evaluate_answers() that:
# 1. Accepts expected_answers and actual_answers as parameters.
# 2. Counts the number of mismatches.
# 3. Calculates the mismatch percentage.
# 4. Returns both values.

def evaluate_answers(expected_answers, actual_answers):
    mismatch = 0
    for ex,ac in zip(expected_answers, actual_answers):
        if ex != ac:
            mismatch = mismatch + 1
    perc=mismatch/len(expected_answers)
    return mismatch,perc

incorrect, percentage = evaluate_answers(
    expected_answers,
    actual_answers
)

print(incorrect, percentage)
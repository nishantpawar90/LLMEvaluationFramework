from itertools import zip_longest

expected_answers = ["New Delhi", "Paris", "Tokyo", "London"]
actual_answers = ["New Delhi", "London", "Tokyo"]

# Expected behavior:
# - Compare answers at matching positions.
# - Count the missing fourth answer as a mismatch.
# - Return the mismatch count and mismatch percentage, using the number of expected answers as the denominator.

mismatch=0
for ex, ac in zip_longest(expected_answers, actual_answers,fillvalue="None"):
    if ex != ac or ac is None:
        print(ex)
        mismatch = mismatch+1

print(mismatch)
print(mismatch/len(expected_answers))

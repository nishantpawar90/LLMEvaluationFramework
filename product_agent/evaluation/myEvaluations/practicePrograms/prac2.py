results = [
    {"test": "TC01", "status": "PASS"},
    {"test": "TC02", "status": "FAIL"},
    {"test": "TC03", "status": "PASS"},
    {"test": "TC04", "status": "FAIL"},
    {"test": "TC05", "status": "PASS"},
    {"test": "TC06", "status": "FAIL"}
]

# Task: Write Python code to calculate and print:
# - Total test cases
# - Number of passed test cases
# - Number of failed test cases
# - Pass percentage

print (len(results))

passed =0
failed =0

for result in results:
    if result["status"] == "PASS":
        passed +=1
    else:
        failed +=1
        print(f"Failed test: {result['test']}")

print(f"Total test cases: {len(results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Pass percentage: {passed / len(results)*100}%")
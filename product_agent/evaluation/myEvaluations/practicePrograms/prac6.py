products = [
    {"name": "Mixed Fruit Jam", "sugar": 9.2},
    {"name": "Apple Jam", "sugar": 7.8},
    {"name": "Mango Jam", "sugar": 10.1},
    {"name": "Blueberry Jam", "sugar": 6.5}
]

agent_response = [
    "Mixed Fruit Jam",
    "Apple Jam",
    "Mango Jam",
    "Blueberry Jam"
]

# Your task: Write code that:
# 1. Identifies which products the agent incorrectly included.
# 2. Prints the incorrect product names.
# 3. Counts the incorrect inclusions.

incorrect_inclusions = 0
for resp, prod in zip(agent_response,products):
    print(prod['name'])
    print(resp)
    product_name = prod['name']
    sugar = prod['sugar']
    if sugar > 10.0:
        incorrect_inclusions = incorrect_inclusions + 1
        print(product_name)




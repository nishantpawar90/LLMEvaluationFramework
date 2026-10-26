products = [
    {"name": "Strawberry Jam", "sugar": 12.5},
    {"name": "Mixed Fruit Jam", "sugar": 9.2},
    {"name": "Apple Jam", "sugar": 7.8},
    {"name": "Mango Jam", "sugar": 10.1}
]

# Write Python code to:
# 1. Find the product with the lowest sugar content.
# 2. Print its name and sugar content.

lowest =100.0
lowest_product = None
for pred  in products:
    if pred["sugar"] < lowest:
        lowest = pred["sugar"]
        lowest_product = pred

print(lowest_product['name'], lowest_product['sugar'])
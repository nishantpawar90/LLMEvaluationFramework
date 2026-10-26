products = [
    {"name": "Strawberry Jam", "sugar": 12.5},
    {"name": "Mixed Fruit Jam", "sugar": 9.2},
    {"name": "Apple Jam", "sugar": 7.8},
    {"name": "Mango Jam", "sugar": 10.1},
    {"name": "Blueberry Jam", "sugar": 6.5}
]

sugar_threshold = 10.0
count = 0
for prod in products:
    if prod["sugar"] < sugar_threshold:
        print(f"{prod['name']} has sugar content below {sugar_threshold} g: {prod['sugar']} g")
        count = count + 1
print(count)
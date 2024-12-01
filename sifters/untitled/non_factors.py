def find_non_factors(numbers):
    non_factors = []
    
    for i, num1 in enumerate(numbers):
        for j, num2 in enumerate(numbers):
            if i != j:  # Avoid comparing a number with itself
                if num1 % num2 != 0 and num2 % num1 != 0:  # Check non-factors
                    pair = tuple(sorted((num1, num2)))  # Sort to avoid duplicate pairs
                    if pair not in non_factors:
                        non_factors.append(pair)
    
    return non_factors

# Example usage
numbers = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
result = find_non_factors(numbers)
print("Pairs of numbers that are not factors of each other:")
for pair in result:
    print(pair)
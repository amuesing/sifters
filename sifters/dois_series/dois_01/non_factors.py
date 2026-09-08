from itertools import combinations

def find_non_factors(numbers):
    non_factors = set()
    
    for num1, num2 in combinations(numbers, 2):  # Generate unique pairs
        print(num1, num2)
        if num1 % num2 != 0 and num2 % num1 != 0:  # Check non-factors
            non_factors.add((num1, num2))
    
    return sorted(non_factors)

# Example usage
numbers = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
result = find_non_factors(numbers)
print("Pairs of numbers that are not factors of each other:")
for pair in result:
    print(pair)
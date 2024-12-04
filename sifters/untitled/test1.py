from itertools import combinations

def find_sieve_factors(numbers):
    sieve_analysis = []  # List to hold results
    
    for num1, num2 in combinations(numbers, 2):  # Generate unique pairs
        if num1 % num2 != 0 and num2 % num1 != 0:  # Check non-factors
            # Define index tuples for each modulo
            indices1 = tuple(range(num1))
            indices2 = tuple(range(num2))
            
            # Compute resulting integers by adding the modulo
            results1 = tuple(i + num1 for i in indices1)
            results2 = tuple(j + num2 for j in indices2)
            
            # Find factors between resulting integers
            factors1_to_2 = [(r1, r2) for r1 in results1 for r2 in results2 if r2 % r1 == 0]
            factors2_to_1 = [(r2, r1) for r2 in results2 for r1 in results1 if r1 % r2 == 0]
            
            # Append analysis
            sieve_analysis.append({
                "pair": (num1, num2),
                "results": (results1, results2),
                "factors1_to_2": factors1_to_2,
                "factors2_to_1": factors2_to_1
            })
    
    return sieve_analysis

# Example usage
numbers = [2, 3, 4]
result = find_sieve_factors(numbers)

# Print results
for analysis in result:
    print(f"Pair: {analysis['pair']}")
    print(f"Results 1: {analysis['results'][0]}")
    print(f"Results 2: {analysis['results'][1]}")
    print(f"Factors from 1 to 2: {analysis['factors1_to_2']}")
    print(f"Factors from 2 to 1: {analysis['factors2_to_1']}")
    print()
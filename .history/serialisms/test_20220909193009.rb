require "./serialisms/index.rb"

fund = 1
range = 24
arr = []

generate_fibonacci_sequence(fund, range, arr)
select_primes(arr)
generate_serial_matrix(arr)

p arr

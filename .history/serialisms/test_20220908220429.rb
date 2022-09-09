require "~/dev/sonic-pi-projects/serialisms/modules.rb"

fund = 1
range = 120
arr = []

generate_fibonacci_sequence(fund, range, arr)
select_primes(arr)

p arr
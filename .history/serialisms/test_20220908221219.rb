require "~/dev/sonic-pi-projects/serialisms/modules.rb"

fund = 1
range = 30
arr = []

generate_fibonacci_sequence(fund, range, arr)
select_primes(arr)
# generate_serial_matrix(arr)

p arr
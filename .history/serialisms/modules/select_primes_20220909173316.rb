def select_primes(arr)
    arr.replace(arr.select {|n| n.prime?})
end
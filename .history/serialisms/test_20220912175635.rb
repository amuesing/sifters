def combos(n,k)
    [*(1..n-k+1)].repeated_combination(5).select { |a| a.reduce(:+) == n }
end

p combos(10,2)
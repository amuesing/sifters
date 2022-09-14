def combos(n,k)
    [*(1..n-k+1)].repeated_combination(3).select { |a| a.reduce(:+) == n }
end

p combos()
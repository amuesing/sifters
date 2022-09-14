def combos(n,k)
    if k == 1
      return [n]
    end
    (1..n-1).flat_map do |i|
      combos(n-i,k-1).map { |r| [i, *r].sort }
    end.uniq
  end

p combos(20, 3)
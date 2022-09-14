# def combos(n,k)
#     if k == 1
#         return [n]
#     end
#     (1..n-1).flat_map do |i|
#       combos(n-i,k-1).map { |r| [i, *r].sort }
#     end.uniq
# end

def combos(n,k,min = 1, cache = {})
    if n < k || n < min
      return []
    end
    cache[[n,k,min]] ||= begin
      if k == 1
        return [n]
      end
      (min..n-1).flat_map do |i|
        combos(n-i,k-1, i, cache).map { |r| [i, *r] }
      end
    end
  end
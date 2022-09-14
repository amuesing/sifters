# def combos(n,k,min = 1, cache = {})
#     if n < k || n < min
#       return []
#     end
#     cache[[n,k,min]] ||= begin
#       if k == 1
#         return [n]
#       end
#       (min..n-1).flat_map do |i|
#         combos(n-i,k-1, i, cache).map { |r| [i, *r] }
#       end
#     end
#   end

perm = function(n, k) {
    grid = matrix(rep(0:n, k), n + 1, k)
    all = expand.grid(data.frame(grid))
    sums = rowSums(all)
    all[sums == n,]
}
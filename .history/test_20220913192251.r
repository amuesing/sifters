perm = function(n, k) {
    grid = matrix(rep(0:n, k), n + 1, k)
    all = expand.grid(data.frame(grid))
    sums = rowSums(all)
    all[sums == n,]
}
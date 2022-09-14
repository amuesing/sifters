comb = function(n, k) {
    all = combn(0:n, k)
    sums = colSums(all)
    all[, sums == n]
}

p comb(4,2)
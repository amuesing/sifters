comb <- function(n, k) {
    all <- combn(0:n, k)
    sums <- colSums(all)
    all[, sums == n]
}

 print(comb(10, 3))
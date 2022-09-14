sum.comb2 <- function(n, k) {
  combos <- 0:n
  sums <- 0:n
  for (width in 2:k) {
    combos <- apply(expand.grid(combos, 0:n), 1, paste, collapse=" ")
    sums <- apply(expand.grid(sums, 0:n), 1, sum)
    if (width == k) {
      return(combos[sums == n])
    } else {
      combos <- combos[sums <= n]
      sums <- sums[sums <= n]
    }
  }
}

# Simple test
print comb2(3, 2)
# [1] "3 0" "2 1" "1 2" "0 3"
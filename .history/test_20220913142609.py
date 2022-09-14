sum.comb3 <- function(n, k) {

   stopifnot(k > 0L)

   REC <- function(n, k) {
      if (k == 1L) list(n) else
      unlist(lapply(0:n, function(i)Map(c, i, REC(n - i, k - 1L))),
             recursive = FALSE)
   }

   matrix(unlist(REC(n, k)), ncol = k, byrow = TRUE)
}

microbenchmark(sum.comb(3, 10), sum.comb2(3, 10), sum.comb3(3, 10))
# Unit: milliseconds
#              expr      min       lq   median       uq      max neval
#  sum.comb2(3, 10) 39.55612 40.60798 41.91954 44.26756 70.44944   100
#  sum.comb3(3, 10) 25.86008 27.74415 28.37080 29.65567 34.18620   100
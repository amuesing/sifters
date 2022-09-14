sum.comb <- function(n,k) { ls1 <- list()                           # generate empty list
 for(i in 1:k) {                        # how could this be done with apply?
    ls1[[i]] <- 0:n                      # fill with 0:n
 }
 allc <- as.matrix(expand.grid(ls1))     # generate all combinations, already using the built in function
 colnames(allc) <- NULL
 index <- (rowSums(allc) == n)       # make index with only the ones that sum to n
 allc[index, ,drop=F]                   # matrix with only the ones that sum to n
 }
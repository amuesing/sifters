def fib_memo(n, memo)
    memo[n] ||= fib_memo(n-1, memo) + fib_memo(n-2, memo)
  end
  
  def fib(n)
    raise "fib not defined for negative numbers" if n < 0
    fib_memo(n, [0, 1])
  end

# fibonacci = Array.new{ |h,k| h[k] = k < 2 ? k : h[k-1] + h[k-2] }
# p fibonacci
# p fibonacci[2]  # => 1
# p fibonacci[23] # => 28657

# fund = 2
# range = 12
# arr = []


# def construct_fibonacci_arr(fund, range, arr)
# i = 0
# y = fund
#     range.times do
#         arr << i
#         i, y = y, i + y
#     end
# end

# construct_fibonacci_arr(fund, range, arr)

# p arr

# Return the nth Fibonacci number

# def find_fib(n)
#     i, y = [0, 1]

#     (n - 1).times do

#         i, y = y, i + y

#     end

#     puts i
# end

# i, y = 0, 1
# same as
# i = 0
# y = 1

# fib(17)
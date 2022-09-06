fund = 2
range = 12
arr = []


def construct_fibonacci_arr(fund, range, arr)

i = 0
y = fund

    range.times do |i|
        arr << i
        i, y = y, i + y
    end

end

construct_fibonacci_arr(fund, range, arr)


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
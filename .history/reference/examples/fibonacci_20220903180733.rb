

i = 0
y = 1

10.times do
    puts i
    i, y = y, i + y
end

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
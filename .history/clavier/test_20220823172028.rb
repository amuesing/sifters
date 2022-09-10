require "matrix"


# a = [6,6], [5, 5]
b = [5,5]

m = Matrix.build(b.length) {b}

# x = Matrix[a]
# y = Matrix[b]

# z = Matrix.combine(x, y) {|x, y| y = x}#{|a, b| a - b} # => Matrix[[5, 4], [1, 0]]

p m
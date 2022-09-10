require "matrix"

a = [6,6]
b = []

x = Matrix[[6, 6]]
y = Matrix[a]

z = Matrix.combine(x, y) {|x, y| y = x}#{|a, b| a - b} # => Matrix[[5, 4], [1, 0]]

p z
require "matrix"



x = Matrix[[6, 6], [4, 4]]
y = Matrix[[1, 2], [3, 4]]

z = Matrix.combine(x, y) {|x, y| y = x}#{|a, b| a - b} # => Matrix[[5, 4], [1, 0]]

p z
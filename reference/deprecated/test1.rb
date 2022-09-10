require 'matrix'

r = [1, 2, 3]

m = Matrix.build(r.length) {|row, col| row - col }
p m

# m = Array.new


# matrix = Matrix.build(r.length) {
# i = 0
# m = []
# while i < r.length
#     x = r[0] - r[i]
#     m << x
#     i += 1
# end
# matrix = m
# }

# p matrix

# p m.each_slice(r.length).to_a

# expecting
# [60, 64, 67, 72, 76],
# [56, 60, 63, 68, 72],
# [53, 57, 60, 65, 69],
# [48, 52, 55, 60, 64],
# [44, 48, 51, 56, 60]

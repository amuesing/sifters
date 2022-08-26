require "matrix"

r = [60, 64, 67, 72, 76]
m = []


def generate_matrix(r, m)
    i = []
    x = []
    y = []

    r.each do |n|
        i << (n - r[0])
        x << Array.new(r.length) {r[0] + (r[0] - n)}
    end

    x.each do |n| 
        y << n.zip(i).map(&:sum)
    end

    y.each do |n|
        n.each do |o|
            m << o
        end
    end
end

generate_matrix(r, m)

z = Matrix.build [m]

# # m.each do |x|
#     Matrix.combine(z, Matrix[m]) {|x, y| m}
# end
p z

# [60, 64, 67, 72, 76],
# [56, 60, 63, 68, 72],
# [53, 57, 60, 65, 69],
# [48, 52, 55, 60, 64],
# [44, 48, 51, 56, 60]
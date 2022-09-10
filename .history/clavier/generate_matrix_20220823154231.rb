require "matrix"

r = [60, 64, 67, 72, 76]
m = []
matrix = Matrix.build(1) {m}


def generate_matrix(r, m)
    i = []
    x = []
    y = []
    z = Matrix[[0, 0]]

    r.each do |n|
        i << (n - r[0])
        x << Array.new(r.length) {r[0] + (r[0] - n)}
    end

    x.each do |n| 
        m << n.zip(i).map(&:sum)
    end

    y.each do |n|
        Matrix.combine(z, Matrix[n]) {n}
    end

    # p z
end

generate_matrix(r, m)

m.each do |x|
    x.each do y
        p Matrix[y]

p m

# [60, 64, 67, 72, 76],
# [56, 60, 63, 68, 72],
# [53, 57, 60, 65, 69],
# [48, 52, 55, 60, 64],
# [44, 48, 51, 56, 60]
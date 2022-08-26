require "matrix"

r = [60, 64, 67, 72, 76]
m = []

def generate_matrix(r, m)
    i = []
    y = []
    r.each do |n|
        i << (n - r.first)
        y << Array.new(r.length) {r.first + (r.first - n)}
    end
    y.each do |n| 
        m << n.zip(i).map(&:sum)
    end
end

def alter_matrix(m, t)
    r = []
    m.each do |n|
        n.each do |z|
            t << z + 5
        end
    end

generate_matrix(r, m)

m = Matrix.rows(m)
n = Matrix[[60, 64, 67, 72, 76]]
p n + m

# [60, 64, 67, 72, 76],
# [56, 60, 63, 68, 72],
# [53, 57, 60, 65, 69],
# [48, 52, 55, 60, 64],
# [44, 48, 51, 56, 60]
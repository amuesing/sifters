require "matrix"

r = [60, 64, 67, 72, 76]
m = []
t = []

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
    m.each do |n|
        n.each do |z|
            t << z + 5
        end
    end
    
end

generate_matrix(r, m)
altered_matrix(m, t)

m = Matrix.rows(m)
n = Matrix.rows(t.each_slice(r.length).to_a)
p m + n

# [60, 64, 67, 72, 76],
# [56, 60, 63, 68, 72],
# [53, 57, 60, 65, 69],
# [48, 52, 55, 60, 64],
# [44, 48, 51, 56, 60]
require "matrix"

r = [60, 64, 67, 72, 76]
m = []
n = []

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

def altered_matrix(m, n)
    m.each do |x|
        x.each do |y|
            t << y + 6
        end
    end
end

generate_matrix(r, m)
altered_matrix(m, t)

m = Matrix.rows(m)
n = Matrix.rows(t.each_slice(r.length).to_a)
p m * n
require "matrix"

row = [60, 64, 67, 72, 76]
matrix = []

m = Matrix[]
# m = Matrix.build(1) {matrix}

def generate_matrix(r, m)
    i = []
    y = []
    rix = Matrix[[0]]


    r.each do |x|
        i << (x - r[0])
        y << Array.new(r.length) {r[0] + (r[0] - x)}
    end
    y.each do |x| 

        trix = Matrix[x.zip(i).map(&:sum)]
        z = Matrix.combine(rix, trix) {|a, b| a = b}

        # z << x.zip(i).map(&:sum)
    #    m << x.zip(i).map(&:sum)
    p z
    end
    # p rix
end

generate_matrix(row, matrix)

# p y
# p m


# expecting
# [60, 64, 67, 72, 76],
# [56, 60, 63, 68, 72],
# [53, 57, 60, 65, 69],
# [48, 52, 55, 60, 64],
# [44, 48, 51, 56, 60]
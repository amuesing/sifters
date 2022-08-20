row = [60, 64, 67, 72, 76]
matrix = []

# build a transposition method which returns a traspositioal matrix given
# an array of integers

def transposition(r, m)
    y = []
    r.each do |t|
        m << r[0] + (r[0] - t)
        y << (t - r[0])
        # m << Array.new(r.length) { x }
        # p y 
    end
    p y
end

transposition(row, matrix)

# p matrix

# expecting
# [60, 64, 67, 72, 76],
# [56, 60, 63, 68, 72],
# [53, 57, 60, 65, 69],
# [48, 52, 55, 60, 64],
# [44, 48, 51, 56, 60]
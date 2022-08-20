
row = [60, 64, 67, 72, 76]
matrix = []
interval = []
sum = []

# build a transposition method which returns a traspositioal matrix given
# an array of integers

def transposition( r, m, i )
    # i = []
    r.each do |x|
        y = r[0] + ( r[0] - x )
        i << ( x - r[0] )
        m << Array.new(r.length) { y }
        # p y 
    end
end

def sum_array ( m, i, s )
    m.each do |int|
        s << int.zip(i).map(&:sum)
    end
end


# def transposition(r, m)
# i = 0
# v = []
#     while i < r.length
#         x = r[0] + (r[0] - r[i])
#         y = (r[i] - r[0])
#         m << Array.new(r.length) { x }
#         v << y
#         i += 1
#     end
# end

transposition(row, matrix, interval)

sum_array( matrix, interval, sum)

p sum

# expecting
# [60, 64, 67, 72, 76],
# [56, 60, 63, 68, 72],
# [53, 57, 60, 65, 69],
# [48, 52, 55, 60, 64],
# [44, 48, 51, 56, 60]
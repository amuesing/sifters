row = [1,2,3,4,5]

def generate_serial_matrix(row)
    interval = []
    y = []
    z = []
    row.each do |tone|
        interval << (tone - row.first)
        y << Array.new(row.length) {row.first + (row.first - n)}
    end
    y.each do |n| 
        z << n.zip(interval).map(&:sum)
    end
    row.replace(z)
end

generate_serial_matrix
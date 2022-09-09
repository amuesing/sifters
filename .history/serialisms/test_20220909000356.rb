def generate_serial_matrix(row)
    x = []
    y = []
    z = []
    row.each do |n|
        x << (n - row.first)
        y << Array.new(row.length) {row.first + (row.first - n)}
    end
    y.each do |n| 
        z << n.zip(x).map(&:sum)
    end
    row.replace(z)
end

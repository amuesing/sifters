def generate_serial_matrix(row)
    interval = []
    y = []
    z = []
    row.each do |note|
        interval << (n - row.first)
        y << Array.new(row.length) {row.first + (row.first - n)}
    end
    y.each do |n| 
        z << n.zip(interval).map(&:sum)
    end
    row.replace(z)
end

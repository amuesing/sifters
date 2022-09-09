def generate_serial_matriinterval(row)
    interval = []
    y = []
    z = []
    row.each do |n|
        interval << (n - row.first)
        y << Array.new(row.length) {row.first + (row.first - n)}
    end
    y.each do |n| 
        z << n.zip(interval).map(&:sum)
    end
    row.replace(z)
end

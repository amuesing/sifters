def generate_serial_matri(row)
     = []
    y = []
    z = []
    row.each do |n|
         << (n - row.first)
        y << Array.new(row.length) {row.first + (row.first - n)}
    end
    y.each do |n| 
        z << n.zip().map(&:sum)
    end
    row.replace(z)
end

def generate_serial_matrix(row)
    interval = []
    collumns = []
    matrix = []
    row.each do |tone|
        interval << (tone - row.first)
        collumns << Array.new(row.length) {row.first + (row.first - tone)}
    end
    collumns.each do |trans| 
        matrix << trans.zip(interval).map(&:sum)
    end
    row.replace(matrix)
end
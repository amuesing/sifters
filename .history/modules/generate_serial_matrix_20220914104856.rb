def generate_serial_matrix(row)
    interval = []
    columns = []
    matrix = []
    row.each do |tone|
        interval << (tone - row.first)
        columns << Array.new(row.length) {row.first + (row.first - tone)}
    end
    columns.each do |trans| 
        matrix << trans.zip(interval).map(&:sum)
    end
    row.replace(matrix)
end